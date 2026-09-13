package com.jvust.book.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;

import com.chaquo.python.Python;

import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final String APP_URL = "http://127.0.0.1:8765/";
    private static final String HEALTH_URL = APP_URL + "api/health";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private WebView webView;
    private TextView statusView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        createContentView();
        executor.execute(this::startBackendAndOpenApp);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void createContentView() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(247, 245, 239));

        webView = new WebView(this);
        webView.setVisibility(WebView.INVISIBLE);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setDatabaseEnabled(true);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                view.setVisibility(WebView.VISIBLE);
                statusView.setVisibility(TextView.GONE);
            }
        });
        root.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        ));

        statusView = new TextView(this);
        statusView.setText("正在启动 Book 学习…");
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
            Python.getInstance()
                    .getModule("android_server")
                    .callAttr("start", getFilesDir().getAbsolutePath());

            for (int attempt = 0; attempt < 120; attempt++) {
                if (backendIsReady()) {
                    mainHandler.post(() -> webView.loadUrl(APP_URL));
                    return;
                }
                Thread.sleep(100L);
            }
            showStartupError("Book 服务启动超时，请重新打开应用");
        } catch (Exception error) {
            showStartupError("Book 服务启动失败，请重新打开应用");
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

    private void showStartupError(String message) {
        mainHandler.post(() -> statusView.setText(message));
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        executor.shutdownNow();
        super.onDestroy();
    }
}
