package com.jvust.book.recorder.data

import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RecordingRepositoryTest {
    @Test
    fun jsonRoundTripPreservesStableEvidenceFields() {
        val original = RecordingMetadata(
            recordingId = "stable-id",
            fileName = "REC_20260830_183000_ab12cd.m4a",
            displayTitle = "Lecture 1",
            createdAtEpochMs = 1234L,
            durationMs = 5678L,
            sizeBytes = 99L,
            courseRef = "functional-analysis",
            sectionRef = "ch01_s01",
            note = "note",
            status = "complete"
        )

        val decoded = RecordingIndex.decode(RecordingIndex.encode(listOf(original))).single()
        assertEquals(original, decoded)
    }

    @Test
    fun editingTitleAndMetadataNeverRenamesPhysicalEvidence() {
        val root = Files.createTempDirectory("book-recorder-test").toFile()
        val recordings = root.resolve("recordings").apply { mkdirs() }
        val repository = RecordingRepository(root.resolve("index.json"), recordings)
        repository.upsert(
            RecordingMetadata(
                recordingId = "stable-id",
                fileName = "REC_20260830_183000_ab12cd.m4a",
                displayTitle = "Original",
                createdAtEpochMs = 1L,
                durationMs = 2L,
                sizeBytes = 3L
            )
        )

        repository.updateDetails("stable-id", "Renamed", "course-a", "section-b", "new note")
        val updated = repository.list().single()

        assertEquals("stable-id", updated.recordingId)
        assertEquals("REC_20260830_183000_ab12cd.m4a", updated.fileName)
        assertEquals("Renamed", updated.displayTitle)
        assertEquals("course-a", updated.courseRef)
        assertEquals("section-b", updated.sectionRef)
        assertEquals("new note", updated.note)
    }

    @Test
    fun reconcileSurfacesOrphanM4aWithoutDeletingIt() {
        val root = Files.createTempDirectory("book-recorder-orphan").toFile()
        val recordings = root.resolve("recordings").apply { mkdirs() }
        val orphan = recordings.resolve("REC_20260830_183000_orphan.m4a")
        orphan.writeBytes(byteArrayOf(1, 2, 3, 4))
        val repository = RecordingRepository(root.resolve("index.json"), recordings)

        val reconciled = repository.reconcile()

        assertEquals(1, reconciled.size)
        assertEquals(orphan.name, reconciled.single().fileName)
        assertEquals("recovered", reconciled.single().status)
        assertTrue(orphan.exists())
    }
}
