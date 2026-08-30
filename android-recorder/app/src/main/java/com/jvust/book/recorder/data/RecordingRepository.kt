package com.jvust.book.recorder.data

import java.io.File
import java.io.FileOutputStream
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.util.UUID

class RecordingRepository(
    private val indexFile: File,
    private val recordingsDir: File
) {
    init {
        indexFile.parentFile?.mkdirs()
        recordingsDir.mkdirs()
    }

    @Synchronized
    fun list(): List<RecordingMetadata> = readIndex().sortedByDescending { it.createdAtEpochMs }

    @Synchronized
    fun upsert(metadata: RecordingMetadata) {
        val records = readIndex().toMutableList()
        val existing = records.indexOfFirst { it.recordingId == metadata.recordingId }
        if (existing >= 0) records[existing] = metadata else records.add(metadata)
        writeIndex(records)
    }

    @Synchronized
    fun updateDetails(
        recordingId: String,
        displayTitle: String,
        courseRef: String,
        sectionRef: String,
        note: String
    ): RecordingMetadata? {
        val records = readIndex().toMutableList()
        val index = records.indexOfFirst { it.recordingId == recordingId }
        if (index < 0) return null
        val current = records[index]
        val updated = current.copy(
            displayTitle = displayTitle.ifBlank { current.displayTitle },
            courseRef = courseRef,
            sectionRef = sectionRef,
            note = note
        )
        records[index] = updated
        writeIndex(records)
        return updated
    }

    @Synchronized
    fun reconcile(): List<RecordingMetadata> {
        val records = readIndex().toMutableList()
        val knownFiles = records.mapTo(mutableSetOf()) { it.fileName }
        recordingsDir.listFiles { file -> file.isFile && file.extension.equals("m4a", ignoreCase = true) }
            ?.sortedBy { it.name }
            ?.forEach { file ->
                if (file.name !in knownFiles) {
                    records.add(
                        RecordingMetadata(
                            recordingId = UUID.nameUUIDFromBytes(file.name.toByteArray(StandardCharsets.UTF_8)).toString(),
                            fileName = file.name,
                            displayTitle = file.nameWithoutExtension,
                            createdAtEpochMs = file.lastModified(),
                            durationMs = 0L,
                            sizeBytes = file.length(),
                            status = "recovered"
                        )
                    )
                    knownFiles.add(file.name)
                }
            }
        writeIndex(records)
        return records.sortedByDescending { it.createdAtEpochMs }
    }

    fun audioFile(metadata: RecordingMetadata): File = File(recordingsDir, metadata.fileName)

    fun audioFile(fileName: String): File = File(recordingsDir, fileName)

    private fun readIndex(): List<RecordingMetadata> {
        if (!indexFile.isFile) return emptyList()
        return runCatching { RecordingIndex.decode(indexFile.readText()) }.getOrElse { emptyList() }
    }

    private fun writeIndex(records: List<RecordingMetadata>) {
        indexFile.parentFile?.mkdirs()
        val temp = File(indexFile.parentFile ?: recordingsDir, "${indexFile.name}.tmp")
        FileOutputStream(temp).use { output ->
            output.write(RecordingIndex.encode(records).toByteArray(StandardCharsets.UTF_8))
            output.fd.sync()
        }
        runCatching {
            Files.move(
                temp.toPath(),
                indexFile.toPath(),
                StandardCopyOption.ATOMIC_MOVE,
                StandardCopyOption.REPLACE_EXISTING
            )
        }.recoverCatching {
            Files.move(temp.toPath(), indexFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
        }.getOrThrow()
    }
}
