// Book Seven portable desktop app. Standard library only; no Node/Python runtime.
package main

import (
	"archive/zip"
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"mime"
	"net"
	"net/http"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

//go:embed content.zip
var content []byte

const buildID = "20261003-windows-1.3.1-study-bridge-r1"
const maxState = 32 * 1024 * 1024
const maxFont = 40 * 1024 * 1024
const csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"

type Envelope struct {
	State    map[string]interface{} `json:"state"`
	Revision int64                  `json:"revision"`
}
type Store struct {
	sync.Mutex
	dir string
	env Envelope
}

func blank() map[string]interface{} {
	return map[string]interface{}{"schema": "book-personal-state-v1", "settings": map[string]interface{}{"fontSize": 20, "fontFamily": "song", "lineHeight": 1.85, "theme": "light"}, "books": map[string]interface{}{}, "notes": map[string]interface{}{}, "bookmarks": map[string]interface{}{}, "cards": map[string]interface{}{}}
}
func valid(v map[string]interface{}) error {
	if v["schema"] != "book-personal-state-v1" {
		return errors.New("瀛︿範鏁版嵁鏍煎紡涓嶆纭?)
	}
	for _, k := range []string{"settings", "books", "notes", "bookmarks", "cards"} {
		if _, ok := v[k].(map[string]interface{}); !ok {
			return fmt.Errorf("瀛︿範鏁版嵁缂哄皯 %s", k)
		}
	}
	for _, bucket := range []string{"books", "notes", "bookmarks", "cards"} {
		for _, val := range v[bucket].(map[string]interface{}) {
			m, ok := val.(map[string]interface{})
			if !ok {
				return fmt.Errorf("%s 鐨勬潯鐩牸寮忎笉姝ｇ‘", bucket)
			}
			for _, key := range []string{"answer", "text", "book_id", "record_id"} {
				if x, exists := m[key]; exists {
					if _, ok := x.(string); !ok {
						return fmt.Errorf("%s 鏂囨湰鏍煎紡涓嶆纭?, key)
					}
				}
			}
		}
	}
	for k := range v {
		if !strings.Contains("|schema|settings|books|notes|bookmarks|cards|", "|"+k+"|") {
			return errors.New("涓嶆敮鎸佺殑瀛︿範鏁版嵁瀛楁")
		}
	}
	var walk func(interface{}, int) error
	walk = func(x interface{}, depth int) error {
		if depth > 20 {
			return errors.New("鏁版嵁宓屽杩囨繁")
		}
		switch y := x.(type) {
		case map[string]interface{}:
			if len(y) > 50000 {
				return errors.New("鏉＄洰杩囧")
			}
			for k, v := range y {
				if k == "__proto__" || k == "constructor" || k == "prototype" {
					return errors.New("涓嶅畨鍏ㄧ殑鏁版嵁瀛楁")
				}
				if e := walk(v, depth+1); e != nil {
					return e
				}
			}
		case []interface{}:
			for _, v := range y {
				if e := walk(v, depth+1); e != nil {
					return e
				}
			}
		}
		return nil
	}
	if e := walk(v, 0); e != nil {
		return e
	}
	b, _ := json.Marshal(v)
	if len(b) > maxState {
		return errors.New("瀛︿範鏁版嵁瓒呰繃 32 MB")
	}
	return nil
}
func newStore(dir string) (*Store, error) {
	if e := os.MkdirAll(dir, 0700); e != nil {
		return nil, e
	}
	s := &Store{dir: dir, env: Envelope{blank(), 0}}
	b, e := os.ReadFile(filepath.Join(dir, "learning.json"))
	if e == nil {
		if e = json.Unmarshal(b, &s.env); e != nil {
			return nil, fmt.Errorf("瀛︿範鏁版嵁鎹熷潖锛屾湭瑕嗙洊鍘熶欢锛?w", e)
		}
		if e = valid(s.env.State); e != nil {
			return nil, e
		}
		if s.env.Revision < 0 {
			return nil, errors.New("瀛︿範鏁版嵁淇鍙锋棤鏁堬紝鏈鐩栧師浠?)
		}
		hist := filepath.Join(dir, "history")
		if e = os.MkdirAll(hist, 0700); e != nil {
			return nil, e
		}
		name := filepath.Join(hist, fmt.Sprintf("before-%s-rev-%010d.json", buildID, s.env.Revision))
		f, err := os.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if err == nil {
			_, err = f.Write(b)
			if err == nil {
				err = f.Sync()
			}
			f.Close()
			if err != nil {
				return nil, err
			}
		} else if !errors.Is(err, os.ErrExist) {
			return nil, err
		}

	} else if !errors.Is(e, os.ErrNotExist) {
		return nil, e
	}
	return s, nil
}
func (s *Store) get() Envelope { s.Lock(); defer s.Unlock(); return s.env }
func (s *Store) put(v map[string]interface{}, revision int64) (Envelope, error) {
	if e := valid(v); e != nil {
		return Envelope{}, e
	}
	s.Lock()
	defer s.Unlock()
	if revision != s.env.Revision {
		return Envelope{}, errors.New("CONFLICT")
	}
	b, _ := json.Marshal(v)
	old, _ := json.Marshal(s.env.State)
	if bytes.Equal(b, old) {
		return s.env, nil
	}
	next := Envelope{v, revision + 1}
	enc, _ := json.Marshal(next)
	if revision%100 == 0 {
		hist := filepath.Join(s.dir, "history")
		if e := os.MkdirAll(hist, 0700); e != nil {
			return Envelope{}, e
		}
		oldEnv, _ := json.Marshal(s.env)
		if e := os.WriteFile(filepath.Join(hist, fmt.Sprintf("state-%010d.json", revision)), oldEnv, 0600); e != nil {
			return Envelope{}, e
		}
	}
	if e := atomicSave(filepath.Join(s.dir, "learning.json"), enc); e != nil {
		return Envelope{}, e
	}
	s.env = next
	return next, nil
}
func atomicSave(name string, data []byte) error {
	tmp := name + ".tmp"
	f, e := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(data)
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e != nil {
		return e
	}
	if ce != nil {
		return ce
	}
	return replaceFile(tmp, name)
}
func respond(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}
func main() {
	if len(os.Args) > 1 && os.Args[1] == "--self-check" {
		v := verifyBundle()
		b, _ := json.MarshalIndent(v, "", "  ")
		name := "Book-SelfCheck.json"
		if len(os.Args) > 2 {
			name = os.Args[2]
		}
		if e := atomicSave(name, b); e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(1)
		}
		fmt.Println(string(b))
		if !v.OK {
			os.Exit(1)
		}
		return
	}

	dir, e := os.UserConfigDir()
	if e != nil {
		message("鏃犳硶鍙栧緱鏈満鏁版嵁鐩綍锛? + e.Error())
		return
	}
	if local := os.Getenv("LOCALAPPDATA"); local != "" {
		dir = local
	}
	dir = filepath.Join(dir, "BookSeven")
	if test := os.Getenv("BOOK_TEST_DATA_DIR"); test != "" {
		dir = test
	}
	if e = os.MkdirAll(dir, 0700); e != nil {
		message(e.Error())
		return
	}
	f, e := os.OpenFile(filepath.Join(dir, "app.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
	if e == nil {
		log.SetOutput(f)
		defer f.Close()
	}
	release, first, e := singleInstance(dir)
	if e != nil {
		message(e.Error())
		return
	}
	if !first {
		b, _ := os.ReadFile(filepath.Join(dir, "server.json"))
		var v map[string]string
		if json.Unmarshal(b, &v) == nil && validServerURL(v["url"]) {
			if v["build"] != buildID {
				message("鍙︿竴涓増鏈殑 Book 浠嶅湪杩愯銆傝鍏堜繚瀛樺涔犺褰曞苟閫€鍑烘棫鐗堬紝鍐嶆墦寮€鏈増锛涙棤闇€鍗歌浇鎴栧垹闄ゅ涔犳暟鎹€?)
				return
			}
			client := &http.Client{Timeout: 2 * time.Second}
			resp, err := client.Get(v["url"] + "api/health")
			if err != nil {
				message("宸叉湁 Book 杩涚▼鏆傛湭灏辩华锛岃绋嶅悗閲嶈瘯锛涘師鏁版嵁鏈敼鍔ㄣ€?)
				return
			}
			resp.Body.Close()
			if resp.StatusCode != 200 {
				message("宸叉湁 Book 鏈嶅姟鏍￠獙澶辫触锛屾湭鎵撳紑鍏朵粬鏈嶅姟銆?)
				return
			}
			if err = openWindow(v["url"]+"document-reader.html", dir); err != nil {
				message(err.Error())
			}
		} else {
			message("Book 姝ｅ湪鍚姩锛岃绋嶅悗鍐嶈瘯銆?)
		}
		return
	}
	defer release()
	store, e := newStore(dir)
	if e != nil {
		message(e.Error())
		return
	}
	z, e := zip.NewReader(bytes.NewReader(content), int64(len(content)))
	if e != nil {
		message("鏁欐潗鍖呮棤娉曡鍙栵細" + e.Error())
		return
	}
	files := map[string]*zip.File{}
	for _, f := range z.File {
		files[f.Name] = f
	}
	if files["data/catalog.json"] == nil {
		message("鏁欐潗鐩綍缂哄け")
		return
	}
	listen := "127.0.0.1:0"
	if port := os.Getenv("BOOK_TEST_PORT"); port != "" {
		listen = "127.0.0.1:" + port
	}
	ln, e := net.Listen("tcp", listen)
	if e != nil {
		message(e.Error())
		return
	}
	host := ln.Addr().String()
	url := "http://" + host + "/"
	tokenBytes := make([]byte, 32)
	if _, e = rand.Read(tokenBytes); e != nil {
		message(e.Error())
		return
	}
	token := hex.EncodeToString(tokenBytes)
	var last atomic.Int64
	last.Store(time.Now().Unix())
	quit := make(chan struct{}, 1)
	mux := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Content-Security-Policy", csp)
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("Cross-Origin-Resource-Policy", "same-origin")
		if r.Host != host || (r.Header.Get("Origin") != "" && r.Header.Get("Origin") != "http://"+host) {
			respond(w, 403, map[string]string{"error": "鍙厑璁告湰鏈哄簲鐢ㄨ闂?})
			return
		}
		last.Store(time.Now().Unix())
		p := r.URL.Path
		if r.Method == http.MethodGet || r.Method == http.MethodHead {
			switch p {
			case "/api/health":
				respond(w, 200, map[string]interface{}{"app": "book-seven", "build": buildID, "ok": true})
				return
			case "/api/session":
				env := store.get()
				respond(w, 200, map[string]interface{}{"state": env.State, "revision": env.Revision, "token": token})
				return
			case "/api/study-progress":
				serveStudyProgress(w, store.get().State)
				return
			case "/api/state":
				respond(w, 200, store.get())
				return
			case "/api/heartbeat":
				respond(w, 200, map[string]bool{"ok": true})
				return
			case "/api/font":
				b, e := os.ReadFile(filepath.Join(dir, "user-font.bin"))
				if e != nil {
					respond(w, 404, map[string]string{"error": "鏈鍏ュ瓧浣?})
					return
				}
				w.Header().Set("Content-Type", "application/octet-stream")
				w.Header().Set("Cache-Control", "no-store")
				w.Header().Set("Content-Length", fmt.Sprint(len(b)))
				if r.Method != "HEAD" {
					w.Write(b)
				}
				return
			}
			name := strings.TrimPrefix(p, "/")
			if name == "" {
				name = "index.html"
			}
			if strings.Contains(name, "\\") || path.Clean(name) != name || strings.HasPrefix(name, "../") {
				respond(w, 404, map[string]string{"error": "璧勬簮涓嶅瓨鍦?})
				return
			}
			f := files[name]
			if f == nil {
				respond(w, 404, map[string]string{"error": "璧勬簮涓嶅瓨鍦?})
				return
			}
			rc, e := f.Open()
			if e != nil {
				respond(w, 500, map[string]string{"error": "璧勬簮鏃犳硶璇诲彇"})
				return
			}
			defer rc.Close()
			if strings.HasPrefix(name, "document-pdfs/") && strings.HasSuffix(name, ".pdf") {
				data, err := io.ReadAll(rc)
				if err != nil {
					respond(w, 500, map[string]string{"error": "鍘?PDF 鏃犳硶璇诲彇"})
					return
				}
				w.Header().Set("Content-Type", "application/pdf")
				w.Header().Set("Cache-Control", "private, max-age=86400")
				http.ServeContent(w, r, path.Base(name), time.Time{}, bytes.NewReader(data))
				return
			}
			typ := mime.TypeByExtension(path.Ext(name))
			if strings.HasSuffix(name, ".js") {
				typ = "text/javascript; charset=utf-8"
			}
			if typ == "" {
				typ = "application/octet-stream"
			}
			w.Header().Set("Content-Type", typ)
			w.Header().Set("Content-Length", fmt.Sprint(f.UncompressedSize64))
			if strings.HasPrefix(name, "media/") || strings.HasPrefix(name, "document-assets/") {
				w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
			} else {
				w.Header().Set("Cache-Control", "no-cache")
			}
			if r.Method != "HEAD" {
				io.Copy(w, rc)
			}
			return
		}
		if r.Method != "POST" {
			respond(w, 405, map[string]string{"error": "涓嶆敮鎸佺殑鎿嶄綔"})
			return
		}
		if r.Header.Get("X-Book-Token") != token {
			respond(w, 403, map[string]string{"error": "浼氳瘽鏍￠獙澶辫触"})
			return
		}
		if p == "/api/quit" {
			respond(w, 200, map[string]bool{"ok": true})
			select {
			case quit <- struct{}{}:
			default:
			}
			return
		}
		if p == "/api/verify" {
			v := verifyBundle()
			respond(w, 200, v)
			return
		}
		lim := int64(maxState + 10000)
		if p == "/api/font" {
			lim = maxFont
		}
		body, e := io.ReadAll(http.MaxBytesReader(w, r.Body, lim))
		if e != nil {
			respond(w, 413, map[string]string{"error": "鏂囦欢澶у皬瓒呭嚭闄愬埗"})
			return
		}
		if p == "/api/font" {
			if len(body) < 4 || (!bytes.Equal(body[:4], []byte{0, 1, 0, 0}) && !strings.Contains("|OTTO|wOFF|wOF2|ttcf|", "|"+string(body[:4])+"|")) {
				respond(w, 400, map[string]string{"error": "涓嶆槸鏀寔鐨勫瓧浣撴枃浠?})
				return
			}
			if e = atomicSave(filepath.Join(dir, "user-font.bin"), body); e != nil {
				respond(w, 500, map[string]string{"error": "瀛椾綋鏃犳硶淇濆瓨"})
				return
			}
			h := sha256.Sum256(body)
			respond(w, 200, map[string]interface{}{"ok": true, "sha256": hex.EncodeToString(h[:])})
			return
		}
		if p != "/api/state" {
			respond(w, 404, map[string]string{"error": "鎺ュ彛涓嶅瓨鍦?})
			return
		}
		if !strings.HasPrefix(r.Header.Get("Content-Type"), "application/json") {
			respond(w, 415, map[string]string{"error": "闇€瑕?JSON"})
			return
		}
		var q struct {
			State    map[string]interface{} `json:"state"`
			Expected int64                  `json:"expected_revision"`
		}
		if e = json.Unmarshal(body, &q); e != nil {
			respond(w, 400, map[string]string{"error": "JSON 鏍煎紡涓嶆纭?})
			return
		}
		env, e := store.put(q.State, q.Expected)
		if e != nil {
			code := 400
			if e.Error() == "CONFLICT" {
				code = 409
			}
			respond(w, code, map[string]string{"error": e.Error()})
			return
		}
		respond(w, 200, env)
	})
	server := &http.Server{Handler: mux, ReadHeaderTimeout: 10 * time.Second, ReadTimeout: 60 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 32 * 1024}
	go func() {
		if e := server.Serve(ln); e != nil && e != http.ErrServerClosed {
			log.Print(e)
		}
	}()
	meta, _ := json.Marshal(map[string]string{"url": url, "build": buildID})
	if e = atomicSave(filepath.Join(dir, "server.json"), meta); e != nil {
		message(e.Error())
		return
	}
	log.Print("Book Seven started ", buildID)
	if os.Getenv("BOOK_TEST_NO_WINDOW") == "" {
		if e = openWindow(url+"document-reader.html", dir); e != nil {
			message("鏃犳硶鎵撳紑搴旂敤绐楀彛銆傝纭鐢佃剳宸插畨瑁?Microsoft Edge銆俓n" + e.Error())
			server.Close()
			return
		}
	}
	// The native process exits after the window stops sending heartbeats for 10 min.
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()
	for {
		select {
		case <-quit:
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			server.Shutdown(ctx)
			cancel()
			return
		case <-ticker.C:
			if time.Now().Unix()-last.Load() > 600 {
				server.Close()
				return
			}
		}
	}
}
func validServerURL(raw string) bool {
	u, e := url.Parse(raw)
	return e == nil && u.Scheme == "http" && u.Hostname() == "127.0.0.1" && u.Port() != "" && u.User == nil && u.RawQuery == "" && u.Fragment == "" && u.Path == "/"
}

