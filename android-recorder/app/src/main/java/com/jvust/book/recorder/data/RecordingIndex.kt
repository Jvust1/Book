package com.jvust.book.recorder.data

import org.json.JSONArray
import org.json.JSONObject

object RecordingIndex {
    private const val SCHEMA_VERSION = 1

    fun encode(records: List<RecordingMetadata>): String {
        val items = JSONArray()
        records.forEach { record ->
            items.put(
                JSONObject()
                    .put("recording_id", record.recordingId)
                    .put("file_name", record.fileName)
                    .put("display_title", record.displayTitle)
                    .put("created_at_epoch_ms", record.createdAtEpochMs)
                    .put("duration_ms", record.durationMs)
                    .put("size_bytes", record.sizeBytes)
                    .put("course_ref", record.courseRef)
                    .put("section_ref", record.sectionRef)
                    .put("note", record.note)
                    .put("status", record.status)
            )
        }
        return JSONObject()
            .put("schema_version", SCHEMA_VERSION)
            .put("recordings", items)
            .toString(2)
    }

    fun decode(text: String): List<RecordingMetadata> {
        if (text.isBlank()) return emptyList()
        val root = JSONObject(text)
        if (root.optInt("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION) return emptyList()
        val items = root.optJSONArray("recordings") ?: return emptyList()
        return buildList {
            for (index in 0 until items.length()) {
                val item = items.optJSONObject(index) ?: continue
                val recordingId = item.optString("recording_id")
                val fileName = item.optString("file_name")
                if (recordingId.isBlank() || fileName.isBlank()) continue
                add(
                    RecordingMetadata(
                        recordingId = recordingId,
                        fileName = fileName,
                        displayTitle = item.optString("display_title", fileName.substringBeforeLast('.')),
                        createdAtEpochMs = item.optLong("created_at_epoch_ms", 0L),
                        durationMs = item.optLong("duration_ms", 0L),
                        sizeBytes = item.optLong("size_bytes", 0L),
                        courseRef = item.optString("course_ref", ""),
                        sectionRef = item.optString("section_ref", ""),
                        note = item.optString("note", ""),
                        status = item.optString("status", "complete")
                    )
                )
            }
        }
    }
}
