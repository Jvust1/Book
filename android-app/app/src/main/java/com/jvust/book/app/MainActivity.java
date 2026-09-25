package com.jvust.book.app;

import android.annotation.SuppressLint;
import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebChromeClient;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.window.OnBackInvokedDispatcher;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.io.*;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    private static final int RECORD_AUDIO_REQUEST = 73;
    private static final String TAG = "BookApp";
    private static final String WEB_STATE = "book.webState";
    private static final String APP_URL = "http://127.0.0.1:8765/";
    private static final String HEALTH_URL = APP_URL + "api/health";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private WebView webView;
    private TextView statusView;
    private Bundle savedWebState;
    private volatile boolean destroyed;
    private boolean pageFailed;
    private JSONObject permissionCommand;
    private JSONObject exportCommand;
    private File webExportFile;
    private String webExportToken;
    private String webExportMime;
    private String webExportName;
    private static final int EXPORT_AUDIO_REQUEST = 74;
    private static final int FILE_CHOOSER_REQUEST = 76;
    private ValueCallback<Uri[]> fileChooserCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        savedWebState = savedInstanceState == null ? null : savedInstanceState.getBundle(WEB_STATE);
        createContentView();
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::navigateBack);
        }
        executor.execute(this::startBackendAndOpenApp);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void createContentView() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(247, 245, 239));
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((view, windowInsets) -> {
                Insets safe = windowInsets.getInsets(WindowInsets.Type.systemBars()
                        | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                view.setPadding(safe.left, safe.top, safe.right, safe.bottom);
                return WindowInsets.CONSUMED;
            });
        }

        webView = new WebView(this);
        webView.setVisibility(WebView.INVISIBLE);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setAllowFileAccess(false);
        // File content is reachable only after an explicit system picker choice.
        webView.getSettings().setAllowContentAccess(true);
        webView.getSettings().setMediaPlaybackRequiresUserGesture(false);
        webView.addJavascriptInterface(new Object() {
            @JavascriptInterface public void request(String json) {
                mainHandler.post(() -> {
                    try {
                        if (!destroyed && webView.getUrl() != null && webView.getUrl().startsWith(APP_URL))
                            recordingCommand(new JSONObject(json));
                    } catch (Exception error) { Log.w(TAG, "Invalid recording request"); }
                });
            }
        }, "BookNative");
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileChooserCallback != null) fileChooserCallback.onReceiveValue(null);
                fileChooserCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), FILE_CHOOSER_REQUEST);
                    return true;
                } catch (ActivityNotFoundException error) {
                    fileChooserCallback = null;
                    Toast.makeText(MainActivity.this, "无法打开文件选择器", Toast.LENGTH_SHORT).show();
                    return false;
                }
            }

            @Override
            public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> {
                    boolean localOrigin = request.getOrigin() != null
                            && "http".equals(request.getOrigin().getScheme())
                            && "127.0.0.1".equals(request.getOrigin().getHost())
                            && request.getOrigin().getPort() == 8765;
                    if (localOrigin && java.util.Arrays.asList(request.getResources()).contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)
                            && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                        request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
                    } else {
                        request.deny();
                    }
                });
            }
        });
        WebView.setWebContentsDebuggingEnabled(
                (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("127.0.0.1".equals(uri.getHost()) && uri.getPort() == 8765
                        && uri.getPath() != null && uri.getPath().startsWith("/__recordings/")) {
                    return recordingAudio(uri.getLastPathSegment(), request.getRequestHeaders().get("Range"));
                }
                return null;
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("http".equals(uri.getScheme()) && "127.0.0.1".equals(uri.getHost())
                        && uri.getPort() == 8765) {
                    return false;
                }
                if ("https".equals(uri.getScheme()) || "http".equals(uri.getScheme())) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    } catch (ActivityNotFoundException error) {
                        Toast.makeText(MainActivity.this, R.string.browser_missing, Toast.LENGTH_SHORT).show();
                    }
                }
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                pageFailed = false;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    pageFailed = true;
                    showStartupError(R.string.page_failed);
                }
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse error) {
                if (request.isForMainFrame()) {
                    pageFailed = true;
                    showStartupError(R.string.page_unavailable);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (!destroyed && !pageFailed) {
                    view.setVisibility(WebView.VISIBLE);
                    statusView.setVisibility(TextView.GONE);
                }
            }
        });
        root.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        statusView = new TextView(this);
        statusView.setText(R.string.starting);
        statusView.setTextSize(18);
        statusView.setTextColor(Color.rgb(54, 83, 20));
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(32, 32, 32, 32);
        root.addView(statusView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        setContentView(root);
    }

    private void recordingCommand(JSONObject command) {
        try {
            String action = command.getString("action");
            String id = command.optString("recordingId");
            if ("state".equals(action)) { reply(command, RecordingService.status(), null); return; }
            if ("list".equals(action)) { reply(command, RecordingFiles.list(this), null); return; }
            if ("begin-web-export".equals(action)) {
                if (exportCommand != null) throw new IOException("已有导出正在进行");
                String mime = command.optString("mimeType").split(";")[0];
                if (!java.util.Arrays.asList("audio/webm", "audio/mp4", "audio/ogg", "audio/wav").contains(mime)) throw new IOException("不支持的音频格式");
                clearWebExport();
                webExportFile = File.createTempFile("book-export-", ".audio", getCacheDir());
                webExportToken = java.util.UUID.randomUUID().toString(); webExportMime = mime;
                String ext = mime.equals("audio/mp4") ? ".m4a" : mime.equals("audio/ogg") ? ".ogg" : mime.equals("audio/wav") ? ".wav" : ".webm";
                webExportName = command.optString("name", "录音").replaceAll("[\\\\/:*?\"<>|]", "_") + ext;
                reply(command, new JSONObject().put("token", webExportToken), null); return;
            }
            if ("append-web-export".equals(action)) {
                if (webExportFile == null || !command.optString("token").equals(webExportToken)) throw new IOException("导出会话已过期");
                if (command.optLong("offset", -1) != webExportFile.length()) throw new IOException("导出数据顺序不一致，请重试");
                String encoded = command.optString("chunk");
                if (encoded.length() > 262144) throw new IOException("导出分片过大");
                try (FileOutputStream out = new FileOutputStream(webExportFile, true)) { out.write(android.util.Base64.decode(encoded, android.util.Base64.DEFAULT)); }
                reply(command, new JSONObject().put("ok", true), null); return;
            }
            if ("export-web".equals(action)) {
                if (webExportFile == null || !command.optString("token").equals(webExportToken) || webExportFile.length() != command.optLong("size")) throw new IOException("导出数据未接收完整");
                if (exportCommand != null) throw new IOException("已有导出正在进行");
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType(webExportMime).putExtra(Intent.EXTRA_TITLE, webExportName);
                startActivityForResult(intent, EXPORT_AUDIO_REQUEST); exportCommand = command; return;
            }
            if ("export-data".equals(action)) {
                if (exportCommand != null) throw new IOException("已有导出正在进行");
                String content = command.optString("content");
                if (content.length() > 5 * 1024 * 1024) throw new IOException("学习进度文件过大");
                clearWebExport();
                webExportFile = File.createTempFile("book-progress-", ".json", getCacheDir());
                try (Writer writer = new OutputStreamWriter(new FileOutputStream(webExportFile), java.nio.charset.StandardCharsets.UTF_8)) {
                    writer.write(content);
                }
                webExportMime = "application/json";
                webExportName = command.optString("name", "book-study-progress.json").replaceAll("[\\\\/:*?\"<>|]", "_");
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType(webExportMime).putExtra(Intent.EXTRA_TITLE, webExportName);
                startActivityForResult(intent, EXPORT_AUDIO_REQUEST); exportCommand = command; return;
            }
            if ("start".equals(action)) {
                if (RecordingService.current != null) throw new IOException("已有录音进行中");
                if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                    if (permissionCommand != null) throw new IOException("正在等待麦克风权限");
                    permissionCommand = command;
                    requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, RECORD_AUDIO_REQUEST);
                    return;
                }
                Intent intent = new Intent(this, RecordingService.class).setAction("start").putExtra("name", command.optString("name"));
                if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent); else startService(intent);
                if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
                    requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 75);
            } else if ("pause".equals(action) || "resume".equals(action) || "stop".equals(action)) {
                RecordingService service = RecordingService.current;
                if (service == null) throw new IOException("当前没有进行中的录音");
                if ("pause".equals(action)) service.pauseCapture();
                if ("resume".equals(action)) service.resumeCapture();
                if ("stop".equals(action)) service.stopCapture();
            } else if ("rename".equals(action)) {
                String title = command.optString("name").trim();
                if (title.isEmpty() || title.length() > 120) throw new IOException("名称请填写 1 至 120 个字符");
                JSONObject row = RecordingFiles.read(this, id); row.put("name", title); RecordingFiles.save(this, row);
            } else if ("archive".equals(action)) {
                JSONObject row = RecordingFiles.read(this, id); row.put("archived", command.optBoolean("archived")); RecordingFiles.save(this, row);
            } else if ("export".equals(action)) {
                if (exportCommand != null) throw new IOException("已有导出正在进行");
                JSONObject row = RecordingFiles.read(this, id);
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("audio/wav")
                        .putExtra(Intent.EXTRA_TITLE, row.optString("name", "录音").replaceAll("[\\\\/:*?\"<>|]", "_") + ".wav");
                startActivityForResult(intent, EXPORT_AUDIO_REQUEST); exportCommand = command; return;
            } else if ("share".equals(action)) {
                RecordingFiles.read(this, id);
                Uri uri = Uri.parse("content://com.jvust.book.app.recordings/" + id);
                Intent send = new Intent(Intent.ACTION_SEND).setType("audio/wav").putExtra(Intent.EXTRA_STREAM, uri)
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                send.setClipData(android.content.ClipData.newRawUri("录音", uri));
                startActivity(Intent.createChooser(send, "分享录音"));
            } else { throw new IOException("不支持的录音操作"); }
            reply(command, new JSONObject().put("ok", true), null);
        } catch (Exception error) { reply(command, null, error.getMessage()); }
    }

    private void reply(JSONObject command, Object result, String error) {
        try {
            JSONObject response = new JSONObject().put("id", command.getString("id"))
                    .put("result", result == null ? JSONObject.NULL : result).put("error", error == null ? JSONObject.NULL : error);
            mainHandler.post(() -> {
                if (!destroyed) webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('book-native-response',{detail:"
                        + response + "}));", null);
            });
        } catch (Exception ignored) { }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == RECORD_AUDIO_REQUEST && permissionCommand != null) {
            JSONObject command = permissionCommand; permissionCommand = null;
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) recordingCommand(command);
            else {
                RecordingService.lastError = "麦克风权限未开启。请在系统设置 → 应用 → Book → 权限中允许麦克风。";
                reply(command, null, RecordingService.lastError);
            }
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST) {
            ValueCallback<Uri[]> callback = fileChooserCallback;
            fileChooserCallback = null;
            if (callback != null) callback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            return;
        }
        if (requestCode != EXPORT_AUDIO_REQUEST || exportCommand == null) return;
        JSONObject command = exportCommand;
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            exportCommand = null; clearWebExport(); reply(command, null, "已取消导出"); return;
        }
        Uri destination = data.getData();
        final File source;
        try {
            String action = command.optString("action");
            source = ("export-web".equals(action) || "export-data".equals(action))
                    ? webExportFile : RecordingFiles.audio(this, command.optString("recordingId"));
        }
        catch (IOException error) { exportCommand = null; reply(command, null, error.getMessage()); return; }
        executor.execute(() -> {
            try (InputStream in = new FileInputStream(source);
                 OutputStream out = getContentResolver().openOutputStream(destination)) {
                if (out == null) throw new IOException("无法写入目标文件");
                byte[] buffer = new byte[65536]; int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
                out.flush(); reply(command, new JSONObject().put("ok", true), null);
            } catch (Exception error) { reply(command, null, "导出失败：" + error.getMessage()); }
            finally { mainHandler.post(() -> { exportCommand = null; clearWebExport(); }); }
        });
    }

    private void clearWebExport() {
        // Only the temporary bridge copy is removed; the IndexedDB original is preserved.
        if (webExportFile != null) webExportFile.delete();
        webExportFile = null; webExportToken = null;
    }

    private WebResourceResponse recordingAudio(String id, String range) {
        try {
            File file = RecordingFiles.audio(this, id);
            if (!file.isFile() || id.equals(RecordingService.activeId())) throw new IOException();
            long length = file.length(), start = 0, end = length - 1;
            if (range != null && range.matches("bytes=\\d+-\\d*")) {
                String[] bounds = range.substring(6).split("-", -1); start = Long.parseLong(bounds[0]);
                if (!bounds[1].isEmpty()) end = Math.min(end, Long.parseLong(bounds[1]));
            }
            if (start > end || start >= length) return new WebResourceResponse("audio/wav", null, 416, "Range Not Satisfiable",
                    java.util.Collections.singletonMap("Content-Range", "bytes */" + length), new ByteArrayInputStream(new byte[0]));
            FileInputStream input = new FileInputStream(file); input.getChannel().position(start);
            final long count = end - start + 1;
            InputStream bounded = new FilterInputStream(input) {
                long remaining = count;
                @Override public int read() throws IOException { if (remaining <= 0) return -1; int v = super.read(); if (v >= 0) remaining--; return v; }
                @Override public int read(byte[] b, int off, int len) throws IOException {
                    if (remaining <= 0) return -1; int n = in.read(b, off, (int) Math.min(len, remaining)); if (n > 0) remaining -= n; return n;
                }
            };
            Map<String, String> headers = new HashMap<>(); headers.put("Accept-Ranges", "bytes");
            headers.put("Content-Length", String.valueOf(count)); headers.put("Cache-Control", "no-store");
            if (range != null) headers.put("Content-Range", "bytes " + start + "-" + end + "/" + length);
            return new WebResourceResponse("audio/wav", null, range == null ? 200 : 206, range == null ? "OK" : "Partial Content", headers, bounded);
        } catch (Exception error) { return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", null, new ByteArrayInputStream(new byte[0])); }
    }

    private void startBackendAndOpenApp() {
        try {
            // Initialization extracts packaged files, so keep it off the UI thread.
            synchronized (MainActivity.class) {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getApplicationContext()));
                }
            }
            if (destroyed) {
                return;
            }
            Python.getInstance()
                    .getModule("android_server")
                    .callAttr("start", getFilesDir().getAbsolutePath());

            long deadline = SystemClock.elapsedRealtime() + 30_000L;
            while (!destroyed && SystemClock.elapsedRealtime() < deadline) {
                if (backendIsReady()) {
                    mainHandler.post(() -> {
                        if (!destroyed) {
                            if (savedWebState == null || webView.restoreState(savedWebState) == null) {
                                webView.loadUrl(APP_URL);
                            }
                            savedWebState = null;
                        }
                    });
                    return;
                }
                Thread.sleep(100L);
            }
            showStartupError(R.string.startup_timeout);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
        } catch (Exception error) {
            Log.e(TAG, "Embedded backend failed to start", error);
            showStartupError(R.string.startup_failed);
        }
    }

    private boolean backendIsReady() {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(HEALTH_URL).openConnection();
            connection.setConnectTimeout(250);
            connection.setReadTimeout(250);
            connection.setUseCaches(false);
            return connection.getResponseCode() == 200;
        } catch (Exception ignored) {
            return false;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void showStartupError(int message) {
        mainHandler.post(() -> {
            if (!destroyed) {
                webView.setVisibility(WebView.INVISIBLE);
                statusView.setVisibility(TextView.VISIBLE);
                statusView.setText(message);
                statusView.setOnClickListener(view -> {
                    statusView.setOnClickListener(null);
                    statusView.setText(R.string.starting);
                    executor.execute(this::startBackendAndOpenApp);
                });
            }
        });
    }

    @Override
    public void onBackPressed() {
        navigateBack();
    }

    private void navigateBack() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            finish();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        Bundle state = new Bundle();
        if (webView.saveState(state) != null) {
            outState.putBundle(WEB_STATE, state);
        } else if (savedWebState != null) {
            outState.putBundle(WEB_STATE, savedWebState);
        }
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        mainHandler.removeCallbacksAndMessages(null);
        executor.shutdownNow();
        if (webView != null) {
            webView.stopLoading();
            ((ViewGroup) webView.getParent()).removeView(webView);
            webView.destroy();
        }
        super.onDestroy();
    }
}
