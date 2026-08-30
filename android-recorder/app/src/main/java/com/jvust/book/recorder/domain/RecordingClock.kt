package com.jvust.book.recorder.domain

class RecordingClock {
    private var accumulatedMs = 0L
    private var activeStartMs: Long? = null

    fun start(nowMs: Long) {
        accumulatedMs = 0L
        activeStartMs = nowMs
    }

    fun pause(nowMs: Long) {
        activeStartMs?.let { start ->
            accumulatedMs += (nowMs - start).coerceAtLeast(0L)
            activeStartMs = null
        }
    }

    fun resume(nowMs: Long) {
        if (activeStartMs == null) {
            activeStartMs = nowMs
        }
    }

    fun elapsed(nowMs: Long): Long {
        val active = activeStartMs?.let { start -> (nowMs - start).coerceAtLeast(0L) } ?: 0L
        return accumulatedMs + active
    }
}
