package com.jvust.book.recorder.domain

enum class RecorderState {
    IDLE,
    RECORDING,
    PAUSED,
    STOPPING,
    ERROR
}

enum class RecorderCommand {
    START,
    PAUSE,
    RESUME,
    STOP,
    STOPPED,
    FAIL,
    RESET
}
