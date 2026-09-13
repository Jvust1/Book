package com.jvust.book.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
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
import android.webkit.WebViewClient;
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

public final class MainActivity extends Activity {
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
        webView.getSettings().setAllowContentAccess(false);
        WebView.setWebContentsDebuggingEnabled(
                (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        webView.setWebViewClient(new WebViewClient() {
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
