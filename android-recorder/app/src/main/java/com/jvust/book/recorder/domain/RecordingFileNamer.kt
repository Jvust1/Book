package com.jvust.book.recorder.domain

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

object RecordingFileNamer {
    private val formatter = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss").withZone(ZoneOffset.UTC)

    fun create(now: Instant, shortId: String): String {
        val safeId = shortId.filter { it.isLetterOrDigit() || it == '-' || it == '_' }.take(12)
            .ifBlank { "recording" }
        return "REC_${formatter.format(now)}_${safeId}.m4a"
    }
}
