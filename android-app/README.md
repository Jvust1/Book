# Book Android APK

This Android Studio project packages the existing Book React/PWA, FastAPI, Python Runtime, and local SQLite StudyRecord into one `arm64-v8a` APK. It does not add or ingest a new structured textbook dataset.

## Build

Prerequisites:

- Android Studio / Android SDK 35
- JDK 17
- Python 3.11 at `C:/Program Files/Python311/python.exe`
- Node.js 22 and npm
- `npm ci` completed once in `app/web`

Open `android-app` in Android Studio, let Gradle sync, and build the `debug` variant. From PowerShell, the equivalent build is:

```powershell
cd app\web
npm ci
cd ..\..\android-app
.\gradlew.bat assembleDebug
```

APK output:

```text
android-app/app/build/outputs/apk/debug/app-debug.apk
```

The APK uses a loopback-only FastAPI server inside the app process. The WebView and API share `http://127.0.0.1:8765`, so the existing relative `/api` contract is preserved. StudyRecord is stored in the app's private internal files directory.
