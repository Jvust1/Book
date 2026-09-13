package com.jvust.book.app;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.media.*;
import android.os.*;
import org.json.JSONObject;
import java.io.*;
import java.util.UUID;

/** Visible, user-controlled microphone service. PCM is flushed as it is captured. */
public final class RecordingService extends Service {
    static volatile RecordingService current;
    static volatile String lastError;
    private static final int NOTICE = 84;
    private static final String CHANNEL = "book-recording";
    private volatile boolean running, paused;
    private volatile long bytes;
    private volatile double level;
    private volatile int captureEpoch;
    private AudioRecord input;
    private Thread worker;
    private PowerManager.WakeLock wakeLock;
    private String id, name;
    private JSONObject metadata;
    private long createdAt;
    private AudioManager audioManager;
    private final AudioManager.OnAudioFocusChangeListener focusListener = change -> {
        if (change < 0 && running && !paused) {
            pauseCapture();
            lastError = "录音因其他音频活动暂停，请返回后继续。";
        }
    };
    static String activeId() { RecordingService s = current; return s != null ? s.id : null; }
    static JSONObject status() throws Exception {
        RecordingService s = current;
        return new JSONObject().put("status", s == null ? "idle" : !s.running ? "saving" : s.paused ? "paused" : "recording")
                .put("durationMs", s == null ? 0 : s.bytes * 1000 / 32000)
                .put("level", s == null ? 0 : s.level)
                .put("name", s == null ? "" : s.name)
                .put("error", lastError == null ? JSONObject.NULL : lastError);
    }
    @Override public IBinder onBind(Intent intent) { return null; }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? "" : intent.getAction();
        if ("pause".equals(action)) pauseCapture();
        else if ("resume".equals(action)) resumeCapture();
        else if ("stop".equals(action)) stopCapture();
        else if (!running && current == null) startCapture(intent == null ? "" : intent.getStringExtra("name"));
        return START_NOT_STICKY;
    }
    @SuppressWarnings("deprecation")
    private void startCapture(String title) {
        current = this;
        lastError = null;
        createdAt = System.currentTimeMillis();
        name = title == null || title.trim().isEmpty() ? "课堂录音" : title.trim();
        id = UUID.randomUUID().toString();
        try {
            if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED)
                throw new SecurityException("麦克风权限未开启");
            NotificationManager notices = getSystemService(NotificationManager.class);
            if (Build.VERSION.SDK_INT >= 26) notices.createNotificationChannel(
                    new NotificationChannel(CHANNEL, "正在录音", NotificationManager.IMPORTANCE_LOW));
            if (Build.VERSION.SDK_INT >= 30) startForeground(NOTICE, notification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            else startForeground(NOTICE, notification());
            if (RecordingFiles.directory(this).getUsableSpace() < 10 * 1024 * 1024) throw new IOException("存储空间不足，请先腾出空间");
            int size = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
            if (size <= 0) throw new IOException("设备不支持当前录音格式");
            input = new AudioRecord(MediaRecorder.AudioSource.MIC, 16000, AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT, Math.max(6400, size * 2));
            if (input.getState() != AudioRecord.STATE_INITIALIZED) throw new IOException("麦克风初始化失败");
            metadata = new JSONObject().put("id", id).put("name", name).put("createdAt", createdAt).put("complete", false);
            RecordingFiles.save(this, metadata);
            audioManager = getSystemService(AudioManager.class);
            if (audioManager.requestAudioFocus(focusListener, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                    != AudioManager.AUDIOFOCUS_REQUEST_GRANTED) throw new IOException("其他应用正在使用音频，请稍后重试");
            input.startRecording();
            if (input.getRecordingState() != AudioRecord.RECORDSTATE_RECORDING) throw new IOException("无法开始录音");
            running = true;
            wakeLock = getSystemService(PowerManager.class).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Book:Recording");
            wakeLock.acquire(24 * 60 * 60 * 1000L);
            worker = new Thread(this::capture, "book-audio");
            worker.start();
            updateNotification();
        } catch (Exception error) { lastError = "录音未开始：" + error.getMessage(); release(); stopSelf(); }
    }
    private void capture() {
        boolean interrupted = false;
        try (RandomAccessFile file = new RandomAccessFile(RecordingFiles.audio(this, id), "rw")) {
            RecordingFiles.header(file);
            byte[] buffer = new byte[3200];
            long lastFlush = 0;
            while (running) {
                if (paused) { Thread.sleep(80); continue; }
                int epoch = captureEpoch;
                int count = input.read(buffer, 0, buffer.length, AudioRecord.READ_BLOCKING);
                synchronized (this) {
                    if (paused || !running || epoch != captureEpoch) continue;
                    if (count < 0) throw new IOException("麦克风连接中断");
                    if (Build.VERSION.SDK_INT >= 29 && input.getActiveRecordingConfiguration() != null
                            && input.getActiveRecordingConfiguration().isClientSilenced()) {
                        pauseCapture(); lastError = "麦克风被系统或其他应用占用，录音已暂停。"; continue;
                    }
                    count -= count % 2;
                    file.write(buffer, 0, count); bytes += count;
                    double sum = 0;
                    for (int i = 0; i < count; i += 2) { short sample = (short) ((buffer[i] & 255) | (buffer[i + 1] << 8)); sum += (double) sample * sample; }
                    level = count == 0 ? 0 : Math.min(1, Math.sqrt(sum / (count / 2)) / 10000);
                }
                if (SystemClock.elapsedRealtime() - lastFlush > 1000) {
                    RecordingFiles.header(file); file.getFD().sync(); lastFlush = SystemClock.elapsedRealtime();
                    if (bytes >= 2_000_000_000L || RecordingFiles.directory(this).getUsableSpace() < 5 * 1024 * 1024)
                        throw new IOException("已到达文件或存储上限");
                }
            }
            RecordingFiles.header(file); file.getFD().sync();
        } catch (Exception error) { interrupted = true; lastError = "录音已中断，已保留收到的音频：" + error.getMessage(); }
        finally {
            try {
                try (RandomAccessFile file = new RandomAccessFile(RecordingFiles.audio(this, id), "rw")) { RecordingFiles.header(file); }
                metadata.put("complete", true).put("interrupted", interrupted);
                RecordingFiles.save(this, metadata);
            } catch (Exception error) { lastError = "录音保存未完成；重开应用可恢复已写入的音频。"; }
            new Handler(Looper.getMainLooper()).post(() -> { release(); stopSelf(); });
        }
    }
    synchronized void pauseCapture() {
        if (!running || paused) return;
        paused = true; level = 0; captureEpoch++;
        try { input.stop(); } catch (IllegalStateException ignored) { }
        updateNotification();
    }
    synchronized void resumeCapture() {
        if (!running || !paused) return;
        try { input.startRecording(); captureEpoch++; paused = false; lastError = null; updateNotification(); }
        catch (Exception error) { lastError = "麦克风仍不可用，请稍后继续。"; }
    }
    synchronized void stopCapture() {
        running = false;
        try { if (input != null) input.stop(); } catch (IllegalStateException ignored) { }
    }
    @SuppressWarnings("deprecation")
    private void release() {
        running = false;
        if (input != null) { input.release(); input = null; }
        if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        if (audioManager != null) audioManager.abandonAudioFocus(focusListener);
        if (current == this) current = null;
        stopForeground(STOP_FOREGROUND_REMOVE);
    }
    private Notification notification() {
        Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent tap = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        return builder.setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentTitle(paused ? "Book · 录音已暂停" : "Book · 正在录音")
                .setContentText(name).setContentIntent(tap).setOngoing(true).setOnlyAlertOnce(true)
                .addAction(new Notification.Action.Builder(null, paused ? "继续" : "暂停", command(paused ? "resume" : "pause", 1)).build())
                .addAction(new Notification.Action.Builder(null, "停止并保存", command("stop", 2)).build()).build();
    }
    private PendingIntent command(String action, int code) {
        return PendingIntent.getService(this, code, new Intent(this, RecordingService.class).setAction(action),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }
    private void updateNotification() { getSystemService(NotificationManager.class).notify(NOTICE, notification()); }
    @Override public void onDestroy() {
        stopCapture();
        // The writer finalizes before releasing AudioRecord; never cut a write in half.
        if (worker == null || !worker.isAlive()) release();
        super.onDestroy();
    }
}
