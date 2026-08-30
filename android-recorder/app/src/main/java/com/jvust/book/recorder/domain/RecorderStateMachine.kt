package com.jvust.book.recorder.domain

class RecorderStateMachine(initialState: RecorderState = RecorderState.IDLE) {
    var state: RecorderState = initialState
        private set

    fun apply(command: RecorderCommand): RecorderState {
        state = when {
            command == RecorderCommand.FAIL -> RecorderState.ERROR
            state == RecorderState.ERROR && command == RecorderCommand.RESET -> RecorderState.IDLE
            state == RecorderState.IDLE && command == RecorderCommand.START -> RecorderState.RECORDING
            state == RecorderState.RECORDING && command == RecorderCommand.PAUSE -> RecorderState.PAUSED
            state == RecorderState.PAUSED && command == RecorderCommand.RESUME -> RecorderState.RECORDING
            state == RecorderState.RECORDING && command == RecorderCommand.STOP -> RecorderState.STOPPING
            state == RecorderState.PAUSED && command == RecorderCommand.STOP -> RecorderState.STOPPING
            state == RecorderState.STOPPING && command == RecorderCommand.STOPPED -> RecorderState.IDLE
            else -> state
        }
        return state
    }
}
