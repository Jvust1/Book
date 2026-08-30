package com.jvust.book.recorder.ui

enum class PlaybackDecision {
    START_NEW,
    TOGGLE_CURRENT,
    STOP_CURRENT_START_NEW
}

class PlaybackSelection {
    private var currentKey: String? = null

    fun select(key: String): PlaybackDecision {
        val decision = when (currentKey) {
            null -> PlaybackDecision.START_NEW
            key -> PlaybackDecision.TOGGLE_CURRENT
            else -> PlaybackDecision.STOP_CURRENT_START_NEW
        }
        currentKey = key
        return decision
    }

    fun current(): String? = currentKey

    fun clear() {
        currentKey = null
    }
}
