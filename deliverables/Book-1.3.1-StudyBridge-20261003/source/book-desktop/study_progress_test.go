package main

import (
	"encoding/json"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func progressFixture(t *testing.T) map[string]interface{} {
	t.Helper()
	raw, err := os.ReadFile(os.Getenv("BOOK_PROGRESS_FIXTURE"))
	if err != nil {
		t.Fatal(err)
	}
	var record struct {
		Snapshots []map[string]interface{} `json:"snapshots"`
	}
	if err = json.Unmarshal(raw, &record); err != nil {
		t.Fatal(err)
	}
	if len(record.Snapshots) != 4 {
		t.Fatal("missing four-mode producer snapshots")
	}
	return map[string]interface{}{"settings": map[string]interface{}{"documentReaderLive": record.Snapshots[1]}, "notes": map[string]interface{}{"secret": "PRIVATE_NOTE_MARKER"}, "cards": map[string]interface{}{"secret": "PRIVATE_ANSWER_MARKER"}}
}

func TestStudyProgressOnlyExportsSnapshot(t *testing.T) {
	state := progressFixture(t)
	w := httptest.NewRecorder()
	serveStudyProgress(w, state)
	if w.Code != 200 || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal(w.Code)
	}
	if strings.Contains(w.Body.String(), "PRIVATE_") || strings.Contains(w.Body.String(), "\"notes\"") {
		t.Fatal("private state exported")
	}
	var p map[string]interface{}
	if json.Unmarshal(w.Body.Bytes(), &p) != nil || p["schema"] != "book.study-progress.v1" {
		t.Fatal("wrong wire format")
	}
}

func TestStudyProgressMissingIsNoContent(t *testing.T) {
	w := httptest.NewRecorder()
	serveStudyProgress(w, blank())
	if w.Code != 204 || w.Body.Len() != 0 {
		t.Fatal("missing snapshot must not expose whole state")
	}
}

func TestStudyProgressRejectsExtraRootOrContextFields(t *testing.T) {
	for _, nested := range []bool{false, true} {
		state := progressFixture(t)
		p := state["settings"].(map[string]interface{})["documentReaderLive"].(map[string]interface{})
		if nested {
			p["context"].(map[string]interface{})["notes"] = "PRIVATE_NOTE_MARKER"
		} else {
			p["notes"] = "PRIVATE_NOTE_MARKER"
		}
		w := httptest.NewRecorder()
		serveStudyProgress(w, state)
		if w.Code != 400 || strings.Contains(w.Body.String(), "PRIVATE_") {
			t.Fatal("extra fields leaked")
		}
	}
}

func TestStudyProgressRejectsNestedOrOversizedScalar(t *testing.T) {
	for _, malicious := range []interface{}{map[string]interface{}{"raw": "PRIVATE_NOTE_MARKER"}, strings.Repeat("x", 161)} {
		state := progressFixture(t)
		p := state["settings"].(map[string]interface{})["documentReaderLive"].(map[string]interface{})
		p["context"].(map[string]interface{})["book_title"] = malicious
		w := httptest.NewRecorder()
		serveStudyProgress(w, state)
		if w.Code != 400 {
			t.Fatal("invalid scalar accepted")
		}
	}
}

