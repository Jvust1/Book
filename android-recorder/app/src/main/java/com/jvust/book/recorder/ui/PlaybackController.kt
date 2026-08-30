package com.jvust.book.recorder.ui

import android.media.MediaPlayer
import java.io.File

class PlaybackController {
    private val selection = PlaybackSelection()
    private var player: MediaPlayer? = null

    fun toggle(file: File, onStateChanged: () -> Unit = {}) {
        when (selection.select(file.absolutePath)) {
            PlaybackDecision.START_NEW,
            PlaybackDecision.STOP_CURRENT_START_NEW -> start(file, onStateChanged)
            PlaybackDecision.TOGGLE_CURRENT -> {
                val active = player
                if (active == null) {
                    start(file, onStateChanged)
                } else if (active.isPlaying) {
                    active.pause()
                    onStateChanged()
                } else {
                    active.start()
                    onStateChanged()
                }
            }
        }
    }

    fun isCurrentPlaying(file: File): Boolean =
        selection.current() == file.absolutePath && player?.isPlaying == true

    fun release() {
        player?.release()
        player = null
        selection.clear()
    }

    private fun start(file: File, onStateChanged: () -> Unit) {
        player?.release()
        player = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnCompletionListener {
                it.release()
                if (player === it) player = null
                selection.clear()
                onStateChanged()
            }
            prepare()
            start()
        }
        onStateChanged()
    }
}
