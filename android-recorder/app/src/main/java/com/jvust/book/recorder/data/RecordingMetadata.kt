package com.jvust.book.recorder.data

data class RecordingMetadata(
    val recordingId: String,
    val fileName: String,
    val displayTitle: String,
    val createdAtEpochMs: Long,
    val durationMs: Long,
    val sizeBytes: Long,
    val courseRef: String = "",
    val sectionRef: String = "",
    val note: String = "",
    val status: String = "complete"
)
