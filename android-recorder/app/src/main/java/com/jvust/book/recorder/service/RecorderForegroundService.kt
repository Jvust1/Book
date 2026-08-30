package com.jvust.book.recorder.service

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.MediaRecorder
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import androidx.core.content.ContextCompat
import com.jvust.book.recorder.MainActivity
import com.jvust.book.recorder.R
import com.jvust.book.recorder.data.RecordingMetadata
import com.jvust.book.recorder.data.RecordingRepository
import com.jvust.book.recorder.data.RecordingStorage
import com.jvust.book.recorder.domain.RecorderCommand
import com.jvust.book.recorder.domain.RecorderState
import com.jvust.book.recorder.domain.RecorderStateMachine
import com.jvust.book.recorder.domain.RecordingClock
import com.jvust.book.recorder.domain.RecordingFileNamer
import java.io.File
import java.time.Instant
import java.util.UUID

class RecorderForegroundService : Service() {
    data class Snapshot(
        val state: RecorderState,
        val elapsedMs: Long,
        val recordingId: String?,
        val title: String?
    )

    inner class LocalBinder : Binder() {
        fun service(): RecorderForegroundService = this@RecorderForegroundService
    }

    private val binder = LocalBinder()
    private val stateMachine = RecorderStateMachine()
    private val clock = RecordingClock()
    private lateinit var repository: RecordingRepository
    private var recorder: MediaRecorder? = null
    private var currentFile: File? = null
    private var currentId: String? = null
    private var currentTitle: String = ""
    private var currentCourse: String = ""
    private var currentSection: String = ""
    private var currentNote: String = ""
    private var currentCreatedAt = 0L
    private var sessionFinalized = true

    override fun onCreate() {
        super.onCreate()
        repository = RecordingStorage.repository(this)
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (RecorderServiceContract.commandForAction(intent?.action)) {
            RecorderCommand.START -> startRecording(intent)
            RecorderCommand.PAUSE -> pauseRecording()
            RecorderCommand.RESUME -> resumeRecording()
            RecorderCommand.STOP -> stopRecording()
            else -> Unit
        }
        return START_NOT_STICKY
    }

    fun snapshot(): Snapshot = Snapshot(
        state = stateMachine.state,
        elapsedMs = when (stateMachine.state) {
            RecorderState.RECORDING, RecorderState.PAUSED, RecorderState.STOPPING -> clock.elapsed(SystemClock.elapsedRealtime())
            else -> 0L
        },
        recordingId = currentId,
        title = currentTitle.takeIf { it.isNotBlank() }
    )

    private fun startRecording(intent: Intent?) {
        if (stateMachine.state == RecorderState.ERROR) stateMachine.apply(RecorderCommand.RESET)
        if (stateMachine.state != RecorderState.IDLE) return
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            stateMachine.apply(RecorderCommand.FAIL)
            return
        }

        val id = UUID.randomUUID().toString()
        val now = System.currentTimeMillis()
        val fileName = RecordingFileNamer.create(Instant.ofEpochMilli(now), id.take(6))
        val file = File(RecordingStorage.recordingsDirectory(this), fileName)
        currentId = id
        currentFile = file
        currentCreatedAt = now
        currentTitle = intent?.getStringExtra(RecorderServiceContract.EXTRA_TITLE)?.trim().orEmpty()
            .ifBlank { "Recording ${fileName.substringBeforeLast('.')}" }
        currentCourse = intent?.getStringExtra(RecorderServiceContract.EXTRA_COURSE_REF)?.trim().orEmpty()
        currentSection = intent?.getStringExtra(RecorderServiceContract.EXTRA_SECTION_REF)?.trim().orEmpty()
        currentNote = intent?.getStringExtra(RecorderServiceContract.EXTRA_NOTE)?.trim().orEmpty()
        sessionFinalized = false

        stateMachine.apply(RecorderCommand.START)
        startRecorderForeground()
        try {
            recorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioChannels(1)
                setAudioSamplingRate(44_100)
                setAudioEncodingBitRate(128_000)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            clock.start(SystemClock.elapsedRealtime())
            refreshNotification()
        } catch (_: Exception) {
            safelyReleaseRecorder()
            recoverCurrentFileIfUseful()
            stateMachine.apply(RecorderCommand.FAIL)
            stopForeground(STOP_FOREGROUND_REMOVE)
        }
    }

    private fun pauseRecording() {
        if (stateMachine.state != RecorderState.RECORDING) return
        try {
            recorder?.pause()
            clock.pause(SystemClock.elapsedRealtime())
            stateMachine.apply(RecorderCommand.PAUSE)
            refreshNotification()
        } catch (_: Exception) {
            stateMachine.apply(RecorderCommand.FAIL)
            refreshNotification()
        }
    }

    private fun resumeRecording() {
        if (stateMachine.state != RecorderState.PAUSED) return
        try {
            recorder?.resume()
            clock.resume(SystemClock.elapsedRealtime())
            stateMachine.apply(RecorderCommand.RESUME)
            refreshNotification()
        } catch (_: Exception) {
            stateMachine.apply(RecorderCommand.FAIL)
            refreshNotification()
        }
    }

    private fun stopRecording() {
        if (stateMachine.state != RecorderState.RECORDING && stateMachine.state != RecorderState.PAUSED) return
        stateMachine.apply(RecorderCommand.STOP)
        val duration = clock.elapsed(SystemClock.elapsedRealtime())
        var cleanStop = false
        try {
            recorder?.stop()
            cleanStop = true
        } catch (_: Exception) {
            cleanStop = false
        } finally {
            safelyReleaseRecorder()
        }

        val file = currentFile
        if (file != null && file.isFile && file.length() > 0L) {
            finalizeMetadata(duration, if (cleanStop) "complete" else "recovered")
        }
        sessionFinalized = true
        stateMachine.apply(RecorderCommand.STOPPED)
        clearSession()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun finalizeMetadata(durationMs: Long, status: String) {
        val file = currentFile ?: return
        val id = currentId ?: return
        repository.upsert(
            RecordingMetadata(
                recordingId = id,
                fileName = file.name,
                displayTitle = currentTitle,
                createdAtEpochMs = currentCreatedAt,
                durationMs = durationMs,
                sizeBytes = file.length(),
                courseRef = currentCourse,
                sectionRef = currentSection,
                note = currentNote,
                status = status
            )
        )
    }

    private fun recoverCurrentFileIfUseful() {
        if (sessionFinalized) return
        val file = currentFile ?: return
        if (file.isFile && file.length() > 0L) {
            finalizeMetadata(clock.elapsed(SystemClock.elapsedRealtime()), "recovered")
            sessionFinalized = true
        }
    }

    private fun safelyReleaseRecorder() {
        runCatching { recorder?.reset() }
        runCatching { recorder?.release() }
        recorder = null
    }

    private fun clearSession() {
        currentFile = null
        currentId = null
        currentTitle = ""
        currentCourse = ""
        currentSection = ""
        currentNote = ""
        currentCreatedAt = 0L
    }

    private fun startRecorderForeground() {
        val notification = buildNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun refreshNotification() {
        getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, buildNotification())
    }

    private fun buildNotification(): Notification {
        val state = stateMachine.state
        val openIntent = PendingIntent.getActivity(
            this,
            10,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val builder = Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle(currentTitle.ifBlank { getString(R.string.app_name) })
            .setContentText(notificationText(state))
            .setContentIntent(openIntent)
            .setOngoing(state == RecorderState.RECORDING || state == RecorderState.PAUSED)
            .setOnlyAlertOnce(true)

        if (state == RecorderState.RECORDING) {
            builder.addAction(
                Notification.Action.Builder(null, getString(R.string.pause), servicePendingIntent(RecorderServiceContract.ACTION_PAUSE, 11)).build()
            )
        } else if (state == RecorderState.PAUSED) {
            builder.addAction(
                Notification.Action.Builder(null, getString(R.string.resume), servicePendingIntent(RecorderServiceContract.ACTION_RESUME, 12)).build()
            )
        }
        if (state == RecorderState.RECORDING || state == RecorderState.PAUSED) {
            builder.addAction(
                Notification.Action.Builder(null, getString(R.string.stop), servicePendingIntent(RecorderServiceContract.ACTION_STOP, 13)).build()
            )
        }
        return builder.build()
    }

    private fun notificationText(state: RecorderState): String {
        val seconds = snapshot().elapsedMs / 1000
        val mm = seconds / 60
        val ss = seconds % 60
        return "${state.name.lowercase().replaceFirstChar { it.uppercase() }} • %02d:%02d".format(mm, ss)
    }

    private fun servicePendingIntent(action: String, requestCode: Int): PendingIntent = PendingIntent.getService(
        this,
        requestCode,
        Intent(this, RecorderForegroundService::class.java).setAction(action),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )

    private fun createNotificationChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, getString(R.string.recording_channel), NotificationManager.IMPORTANCE_LOW)
        )
    }

    override fun onDestroy() {
        if (!sessionFinalized) recoverCurrentFileIfUseful()
        safelyReleaseRecorder()
        super.onDestroy()
    }

    companion object {
        private const val CHANNEL_ID = "book_recorder_active"
        private const val NOTIFICATION_ID = 1001
    }
}
