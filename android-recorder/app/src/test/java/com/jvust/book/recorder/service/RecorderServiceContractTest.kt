package com.jvust.book.recorder.service

import com.jvust.book.recorder.domain.RecorderCommand
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RecorderServiceContractTest {
    @Test
    fun serviceActionsMapToExactlyOneRecorderCommand() {
        assertEquals(RecorderCommand.START, RecorderServiceContract.commandForAction(RecorderServiceContract.ACTION_START))
        assertEquals(RecorderCommand.PAUSE, RecorderServiceContract.commandForAction(RecorderServiceContract.ACTION_PAUSE))
        assertEquals(RecorderCommand.RESUME, RecorderServiceContract.commandForAction(RecorderServiceContract.ACTION_RESUME))
        assertEquals(RecorderCommand.STOP, RecorderServiceContract.commandForAction(RecorderServiceContract.ACTION_STOP))
        assertNull(RecorderServiceContract.commandForAction("unknown"))
    }
}
