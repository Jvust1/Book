package com.jvust.book.recorder.service

import com.jvust.book.recorder.domain.RecorderCommand

object RecorderServiceContract {
    const val ACTION_START = "com.jvust.book.recorder.action.START"
    const val ACTION_PAUSE = "com.jvust.book.recorder.action.PAUSE"
    const val ACTION_RESUME = "com.jvust.book.recorder.action.RESUME"
    const val ACTION_STOP = "com.jvust.book.recorder.action.STOP"

    const val EXTRA_TITLE = "title"
    const val EXTRA_COURSE_REF = "course_ref"
    const val EXTRA_SECTION_REF = "section_ref"
    const val EXTRA_NOTE = "note"

    fun commandForAction(action: String?): RecorderCommand? = when (action) {
        ACTION_START -> RecorderCommand.START
        ACTION_PAUSE -> RecorderCommand.PAUSE
        ACTION_RESUME -> RecorderCommand.RESUME
        ACTION_STOP -> RecorderCommand.STOP
        else -> null
    }
}
