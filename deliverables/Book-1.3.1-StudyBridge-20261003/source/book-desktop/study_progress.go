package main

import (
	"encoding/json"
	"errors"
	"net/http"
)

// Export ONLY the bounded progress record. Never hand mygpt the whole state,
// personal notes, saved drafts, bookmarks, answers or source document bodies.
func studyRecord(value interface{}, fields []string) (map[string]interface{}, error) {
	input, ok := value.(map[string]interface{})
	if !ok || len(input) != len(fields) {
		return nil, errors.New("invalid progress field set")
	}
	output := make(map[string]interface{}, len(fields))
	for _, key := range fields {
		value, exists := input[key]
		if !exists {
			return nil, errors.New("missing progress field")
		}
		if key == "context" && value != nil {
			context, err := studyRecord(value, []string{"book_id", "book_title", "document_id", "chapter", "mode", "source_sha256", "block_id", "content_offset", "block_index", "block_count", "position_fraction", "rendered_page", "rendered_page_count", "font_px", "practice_answered", "practice_total", "fullscreen"})
			if err != nil {
				return nil, err
			}
			output[key] = context
			continue
		}
		switch value := value.(type) {
		case string:
			if len([]rune(value)) > 160 {
				return nil, errors.New("oversized progress string")
			}
			output[key] = value
		case float64, int, int64, bool, nil:
			output[key] = value
		default:
			return nil, errors.New("invalid progress scalar")
		}
	}
	return output, nil
}

func serveStudyProgress(w http.ResponseWriter, state map[string]interface{}) {
	w.Header().Set("Cache-Control", "no-store")
	settings, ok := state["settings"].(map[string]interface{})
	if !ok || settings["documentReaderLive"] == nil {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	progress, err := studyRecord(settings["documentReaderLive"], []string{"schema", "producer_session", "sequence", "captured_at", "expires_at", "status", "visible_seconds", "idle_seconds", "can_interact", "context"})
	if err != nil || progress["schema"] != "book.study-progress.v1" {
		respond(w, http.StatusBadRequest, map[string]string{"error": "invalid progress record"})
		return
	}
	body, err := json.Marshal(progress)
	if err != nil || len(body) > 8192 {
		respond(w, http.StatusBadRequest, map[string]string{"error": "invalid progress record"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	w.Write(body)
}

