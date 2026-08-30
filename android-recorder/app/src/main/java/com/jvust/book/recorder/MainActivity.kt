package com.jvust.book.recorder

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.jvust.book.recorder.data.RecordingMetadata
import com.jvust.book.recorder.data.RecordingRepository
import com.jvust.book.recorder.data.RecordingStorage
import com.jvust.book.recorder.domain.RecorderState
import com.jvust.book.recorder.service.RecorderForegroundService
import com.jvust.book.recorder.service.RecorderServiceContract
import com.jvust.book.recorder.ui.PlaybackController
import com.jvust.book.recorder.ui.RecordingAdapter

class MainActivity : Activity() {
    private lateinit var repository: RecordingRepository
    private lateinit var adapter: RecordingAdapter
    private val playback = PlaybackController()
    private val handler = Handler(Looper.getMainLooper())
    private var recorderService: RecorderForegroundService? = null
    private var bound = false
    private var pendingStart = false

    private lateinit var stateText: TextView
    private lateinit var timerText: TextView
    private lateinit var titleInput: EditText
    private lateinit var courseInput: EditText
    private lateinit var sectionInput: EditText
    private lateinit var noteInput: EditText
    private lateinit var startButton: Button
    private lateinit var pauseButton: Button
    private lateinit var stopButton: Button

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            recorderService = (binder as? RecorderForegroundService.LocalBinder)?.service()
            bound = recorderService != null
            renderServiceState()
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            recorderService = null
            bound = false
        }
    }

    private val ticker = object : Runnable {
        override fun run() {
            renderServiceState()
            handler.postDelayed(this, 500L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        repository = RecordingStorage.repository(this)
        bindViews()
        adapter = RecordingAdapter(
            context = this,
            onPlay = { record -> play(record) },
            onEdit = { record -> showEditDialog(record) },
            onShare = { record -> share(record) }
        )
        findViewById<ListView>(R.id.recordingList).adapter = adapter
        refreshLibrary()

        startButton.setOnClickListener { requestStart() }
        pauseButton.setOnClickListener { togglePause() }
        stopButton.setOnClickListener { sendServiceAction(RecorderServiceContract.ACTION_STOP) }
    }

    override fun onStart() {
        super.onStart()
        bindService(Intent(this, RecorderForegroundService::class.java), serviceConnection, Context.BIND_AUTO_CREATE)
        handler.post(ticker)
    }

    override fun onStop() {
        handler.removeCallbacks(ticker)
        if (bound) {
            unbindService(serviceConnection)
            bound = false
            recorderService = null
        }
        super.onStop()
    }

    override fun onDestroy() {
        playback.release()
        super.onDestroy()
    }

    private fun bindViews() {
        stateText = findViewById(R.id.stateText)
        timerText = findViewById(R.id.timerText)
        titleInput = findViewById(R.id.titleInput)
        courseInput = findViewById(R.id.courseInput)
        sectionInput = findViewById(R.id.sectionInput)
        noteInput = findViewById(R.id.noteInput)
        startButton = findViewById(R.id.startButton)
        pauseButton = findViewById(R.id.pauseButton)
        stopButton = findViewById(R.id.stopButton)
    }

    private fun requestStart() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            beginRecording()
            return
        }
        pendingStart = true
        val permissions = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT >= 33) permissions += Manifest.permission.POST_NOTIFICATIONS
        requestPermissions(permissions.toTypedArray(), REQUEST_RECORD_AUDIO)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != REQUEST_RECORD_AUDIO || !pendingStart) return
        pendingStart = false
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            beginRecording()
        } else {
            Toast.makeText(this, R.string.microphone_permission_required, Toast.LENGTH_LONG).show()
            stateText.text = getString(R.string.state_permission_denied)
        }
    }

    private fun beginRecording() {
        val intent = Intent(this, RecorderForegroundService::class.java)
            .setAction(RecorderServiceContract.ACTION_START)
            .putExtra(RecorderServiceContract.EXTRA_TITLE, titleInput.text.toString())
            .putExtra(RecorderServiceContract.EXTRA_COURSE_REF, courseInput.text.toString())
            .putExtra(RecorderServiceContract.EXTRA_SECTION_REF, sectionInput.text.toString())
            .putExtra(RecorderServiceContract.EXTRA_NOTE, noteInput.text.toString())
        ContextCompat.startForegroundService(this, intent)
    }

    private fun togglePause() {
        when (recorderService?.snapshot()?.state) {
            RecorderState.RECORDING -> sendServiceAction(RecorderServiceContract.ACTION_PAUSE)
            RecorderState.PAUSED -> sendServiceAction(RecorderServiceContract.ACTION_RESUME)
            else -> Unit
        }
    }

    private fun sendServiceAction(action: String) {
        startService(Intent(this, RecorderForegroundService::class.java).setAction(action))
    }

    private fun renderServiceState() {
        val snapshot = recorderService?.snapshot()
        val state = snapshot?.state ?: RecorderState.IDLE
        stateText.text = getString(R.string.state_format, state.name.lowercase().replaceFirstChar { it.uppercase() })
        timerText.text = formatDuration(snapshot?.elapsedMs ?: 0L)
        startButton.isEnabled = state == RecorderState.IDLE || state == RecorderState.ERROR
        pauseButton.isEnabled = state == RecorderState.RECORDING || state == RecorderState.PAUSED
        pauseButton.text = if (state == RecorderState.PAUSED) getString(R.string.resume) else getString(R.string.pause)
        stopButton.isEnabled = state == RecorderState.RECORDING || state == RecorderState.PAUSED
        if (state == RecorderState.IDLE) refreshLibrary()
    }

    private fun refreshLibrary() {
        val records = runCatching { repository.reconcile() }.getOrElse {
            Toast.makeText(this, R.string.library_read_failed, Toast.LENGTH_SHORT).show()
            repository.list()
        }
        adapter.submit(records)
    }

    private fun play(record: RecordingMetadata) {
        val file = repository.audioFile(record)
        if (!file.isFile || file.length() == 0L) {
            Toast.makeText(this, R.string.audio_file_missing, Toast.LENGTH_SHORT).show()
            return
        }
        runCatching { playback.toggle(file) { adapter.notifyDataSetChanged() } }
            .onFailure { Toast.makeText(this, R.string.playback_failed, Toast.LENGTH_SHORT).show() }
    }

    private fun showEditDialog(record: RecordingMetadata) {
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(36, 8, 36, 0)
        }
        val title = EditText(this).apply { hint = getString(R.string.title_hint); setText(record.displayTitle) }
        val course = EditText(this).apply { hint = getString(R.string.course_hint); setText(record.courseRef) }
        val section = EditText(this).apply { hint = getString(R.string.section_hint); setText(record.sectionRef) }
        val note = EditText(this).apply { hint = getString(R.string.note_hint); setText(record.note) }
        listOf(title, course, section, note).forEach(container::addView)

        AlertDialog.Builder(this)
            .setTitle(R.string.edit_recording)
            .setView(container)
            .setNegativeButton(android.R.string.cancel, null)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                repository.updateDetails(
                    record.recordingId,
                    title.text.toString(),
                    course.text.toString(),
                    section.text.toString(),
                    note.text.toString()
                )
                refreshLibrary()
            }
            .show()
    }

    private fun share(record: RecordingMetadata) {
        val file = repository.audioFile(record)
        if (!file.isFile) return
        val uri = FileProvider.getUriForFile(this, "$packageName.files", file)
        val intent = Intent(Intent.ACTION_SEND)
            .setType("audio/mp4")
            .putExtra(Intent.EXTRA_STREAM, uri)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        startActivity(Intent.createChooser(intent, getString(R.string.share_recording)))
    }

    private fun formatDuration(ms: Long): String {
        val seconds = ms / 1000
        val hours = seconds / 3600
        val minutes = (seconds % 3600) / 60
        val secs = seconds % 60
        return if (hours > 0) "%02d:%02d:%02d".format(hours, minutes, secs) else "%02d:%02d".format(minutes, secs)
    }

    companion object {
        private const val REQUEST_RECORD_AUDIO = 2001
    }
}
