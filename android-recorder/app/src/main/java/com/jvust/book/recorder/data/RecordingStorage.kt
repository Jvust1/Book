package com.jvust.book.recorder.data

import android.content.Context
import android.os.Environment
import java.io.File

object RecordingStorage {
    fun recordingsDirectory(context: Context): File {
        val musicRoot = context.getExternalFilesDir(Environment.DIRECTORY_MUSIC)
        val root = musicRoot ?: context.filesDir
        return File(root, "book-recordings").apply { mkdirs() }
    }

    fun repository(context: Context): RecordingRepository = RecordingRepository(
        indexFile = File(context.filesDir, "recordings-index-v1.json"),
        recordingsDir = recordingsDirectory(context)
    )
}
