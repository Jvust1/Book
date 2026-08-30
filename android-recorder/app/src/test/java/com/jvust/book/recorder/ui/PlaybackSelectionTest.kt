package com.jvust.book.recorder.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PlaybackSelectionTest {
    @Test
    fun selectingSecondRecordingStopsFirstBeforeStartingSecond() {
        val selection = PlaybackSelection()
        assertEquals(PlaybackDecision.START_NEW, selection.select("a.m4a"))
        assertEquals("a.m4a", selection.current())
        assertEquals(PlaybackDecision.STOP_CURRENT_START_NEW, selection.select("b.m4a"))
        assertEquals("b.m4a", selection.current())
        assertEquals(PlaybackDecision.TOGGLE_CURRENT, selection.select("b.m4a"))
        selection.clear()
        assertNull(selection.current())
    }
}
