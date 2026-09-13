package com.jvust.book.app;

import android.content.Context;
import android.util.AtomicFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Private audio originals and atomic, recoverable metadata. */
final class RecordingFiles {
    static final int SAMPLE_RATE = 16000;
    static File directory(Context context) throws IOException {
        File dir = new File(context.getFilesDir(), "recordings");
        if (!dir.isDirectory() && !dir.mkdirs()) throw new IOException("无法创建录音目录");
        return dir;
    }
    static File audio(Context context, String id) throws IOException {
        if (id == null || !id.matches("[a-f0-9-]{36}")) throw new IOException("录音地址无效");
        return new File(directory(context), id + ".wav");
    }
    static synchronized void save(Context context, JSONObject value) throws Exception {
        String id = value.getString("id");
        audio(context, id);
        AtomicFile file = new AtomicFile(new File(directory(context), id + ".json"));
        FileOutputStream stream = null;
        try {
            stream = file.startWrite();
            stream.write(value.toString().getBytes(StandardCharsets.UTF_8));
            file.finishWrite(stream);
        } catch (Exception error) { if (stream != null) file.failWrite(stream); throw error; }
    }
    static synchronized JSONObject read(Context context, String id) throws Exception {
        audio(context, id);
        AtomicFile file = new AtomicFile(new File(directory(context), id + ".json"));
        return new JSONObject(new String(file.readFully(), StandardCharsets.UTF_8));
    }
    static synchronized JSONArray list(Context context) throws Exception {
        List<JSONObject> entries = new ArrayList<>();
        File[] files = directory(context).listFiles((dir, name) -> name.endsWith(".wav"));
        if (files != null) for (File file : files) {
            String id = file.getName().replace(".wav", "");
            if (id.equals(RecordingService.activeId())) continue;
            if (file.length() <= 44) continue;
            JSONObject row;
            try { row = read(context, id); }
            catch (Exception error) {
                row = new JSONObject().put("id", id).put("name", "恢复的录音")
                        .put("createdAt", file.lastModified()).put("complete", false);
            }
            if (!row.optBoolean("complete")) {
                try (RandomAccessFile wav = new RandomAccessFile(file, "rw")) { header(wav); }
                row.put("complete", true).put("interrupted", true);
                save(context, row);
            }
            row.put("durationMs", (file.length() - 44) * 1000 / (SAMPLE_RATE * 2));
            row.put("size", file.length()).put("mimeType", "audio/wav").put("native", true);
            entries.add(row);
        }
        entries.sort((a, b) -> Long.compare(b.optLong("createdAt"), a.optLong("createdAt")));
        return new JSONArray(entries);
    }
    static void header(RandomAccessFile file) throws IOException {
        long bytes = Math.max(0, file.length() - 44);
        file.seek(0);
        file.writeBytes("RIFF"); le(file, bytes + 36, 4); file.writeBytes("WAVEfmt ");
        le(file, 16, 4); le(file, 1, 2); le(file, 1, 2);
        le(file, SAMPLE_RATE, 4); le(file, SAMPLE_RATE * 2, 4);
        le(file, 2, 2); le(file, 16, 2); file.writeBytes("data"); le(file, bytes, 4);
        file.seek(file.length());
    }
    private static void le(RandomAccessFile file, long value, int count) throws IOException {
        for (int i = 0; i < count; i++) file.write((int) (value >> (8 * i)) & 255);
    }
}
