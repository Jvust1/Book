# Book Windows desktop app

The Windows build packages the local FastAPI runtime, React interface, current canonical Functional Analysis assets and a native Edge WebView2 window into one x64 executable. It does not require Python, Node.js or a separately started server after packaging.

Run `desktop-app/build.ps1` from PowerShell. The reproducible build uses Python 3.11, installs pinned desktop-packaging dependencies into `.venv-desktop`, runs `npm ci`, builds the frontend in desktop mode and emits:

```text
dist/Book-0.1.4-Windows-x64.exe
```

Study progress is stored at `%LOCALAPPDATA%\BookApp\book-app.sqlite3`. WebView2 state, including browser-format recordings, is stored under `%LOCALAPPDATA%\BookApp\WebView2`. Logs are written to `%LOCALAPPDATA%\BookApp\logs\desktop.log`.

The app binds only to `127.0.0.1:17866`. A second instance is rejected so that both processes cannot write the same local profile. Edge WebView2 Runtime is required; it is normally present on supported Windows 10/11 systems. The desktop build does not request microphone permission and its recording control is disabled; use the Android app for recording. Downloads use the Windows save dialog.

The bundled textbook, formulas and learning UI use the same release source as Android. Study progress is stored locally on each device. Use the in-app “同步” page to export a JSON progress file, transfer it by any method, and import it on the other device. Newer records win; recordings and textbook files are excluded. No account, model, API or cloud service is required.
