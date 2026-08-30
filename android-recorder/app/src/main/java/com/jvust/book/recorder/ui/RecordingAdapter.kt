package com.jvust.book.recorder.ui

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.TextView
import com.jvust.book.recorder.R
import com.jvust.book.recorder.data.RecordingMetadata
import java.text.DateFormat
import java.util.Date

class RecordingAdapter(
    context: Context,
    private val onPlay: (RecordingMetadata) -> Unit,
    private val onEdit: (RecordingMetadata) -> Unit,
    private val onShare: (RecordingMetadata) -> Unit
) : BaseAdapter() {
    private val inflater = LayoutInflater.from(context)
    private var records: List<RecordingMetadata> = emptyList()

    fun submit(records: List<RecordingMetadata>) {
        this.records = records
        notifyDataSetChanged()
    }

    override fun getCount(): Int = records.size
    override fun getItem(position: Int): RecordingMetadata = records[position]
    override fun getItemId(position: Int): Long = position.toLong()

    override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
        val view = convertView ?: inflater.inflate(R.layout.item_recording, parent, false)
        val record = getItem(position)
        view.findViewById<TextView>(R.id.recordingTitle).text = record.displayTitle
        view.findViewById<TextView>(R.id.recordingMeta).text = buildString {
            append(DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(record.createdAtEpochMs)))
            append(" • ")
            append(formatDuration(record.durationMs))
            append(" • ")
            append(formatBytes(record.sizeBytes))
            if (record.status != "complete") append(" • ${record.status}")
        }
        view.findViewById<TextView>(R.id.recordingDetails).text = listOf(
            record.courseRef.takeIf { it.isNotBlank() }?.let { "Course: $it" },
            record.sectionRef.takeIf { it.isNotBlank() }?.let { "Section: $it" },
            record.note.takeIf { it.isNotBlank() }
        ).filterNotNull().joinToString("\n").ifBlank { "No course metadata" }
        view.findViewById<Button>(R.id.playButton).setOnClickListener { onPlay(record) }
        view.findViewById<Button>(R.id.editButton).setOnClickListener { onEdit(record) }
        view.findViewById<Button>(R.id.shareButton).setOnClickListener { onShare(record) }
        return view
    }

    private fun formatDuration(ms: Long): String {
        val seconds = ms / 1000
        return "%02d:%02d".format(seconds / 60, seconds % 60)
    }

    private fun formatBytes(bytes: Long): String = when {
        bytes >= 1024 * 1024 -> "%.1f MB".format(bytes / (1024.0 * 1024.0))
        bytes >= 1024 -> "%.1f KB".format(bytes / 1024.0)
        else -> "$bytes B"
    }
}
