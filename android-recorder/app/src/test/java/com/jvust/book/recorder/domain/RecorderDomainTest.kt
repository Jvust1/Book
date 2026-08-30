package com.jvust.book.recorder.domain

import java.time.Instant
import org.junit.Assert.assertEquals
import org.junit.Test

class RecorderDomainTest {
    @Test
    fun duplicateStartDoesNotCreateSecondRecorderState() {
        val machine = RecorderStateMachine()
        assertEquals(RecorderState.RECORDING, machine.apply(RecorderCommand.START))
        assertEquals(RecorderState.RECORDING, machine.apply(RecorderCommand.START))
    }

    @Test
    fun pauseResumeAndStopFollowAllowedTransitions() {
        val machine = RecorderStateMachine()
        machine.apply(RecorderCommand.START)
        assertEquals(RecorderState.PAUSED, machine.apply(RecorderCommand.PAUSE))
        assertEquals(RecorderState.RECORDING, machine.apply(RecorderCommand.RESUME))
        assertEquals(RecorderState.STOPPING, machine.apply(RecorderCommand.STOP))
        assertEquals(RecorderState.IDLE, machine.apply(RecorderCommand.STOPPED))
    }

    @Test
    fun elapsedTimeExcludesPauseWindow() {
        val clock = RecordingClock()
        clock.start(1_000)
        clock.pause(4_000)
        clock.resume(9_000)
        assertEquals(5_000, clock.elapsed(11_000))
    }

    @Test
    fun generatedFilenameIsDeterministicAndM4a() {
        assertEquals(
            "REC_20260830_183000_ab12cd.m4a",
            RecordingFileNamer.create(Instant.parse("2026-08-30T18:30:00Z"), "ab12cd")
        )
    }
}
