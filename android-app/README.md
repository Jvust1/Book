# Book Android APK

Book 学习 0.1.4（versionCode 5）新增手动学习进度传输。打开“同步”导出 JSON 文件，直接传到另一台设备后导入；较新的记录优先，重复导入安全，录音不会进入同步包。详见 [手动同步说明](../docs/MANUAL_PROGRESS_SYNC.md)。

适用于 Android 7.0（API 24）及以上的 ARM64 手机和 x86_64 模拟器。
安装包内包含 React 页面、FastAPI、Python Runtime 和 SQLite，无需另开电脑服务器。

教材库、章节浏览、预习/学习/复习/刷题、教材搜索、来源查看和学习进度可离线使用。
本次仅打包仓库已有的泛函分析教材，未增加结构化数据。
安装包未配置问答模型或 API 密钥；问答会显示模型未配置，其他功能可正常使用。

## 0.1.3 更新

- 教材、搜索结果、来源和问答文本支持 Markdown / LaTeX，KaTeX 字体随包离线提供；长公式独立横向滚动，无法解析时显示原文。
- 统一纸白、浅绿和深绿页面，优化手机导航、课程卡片、公式阅读和录音控制。
- 录音使用 Android 原生前台服务，支持锁屏/切换应用、暂停/继续、通知栏控制、停止保存、音量反馈。
- 保存后可播放、拖动进度、调整速度、搜索、重命名、归档/恢复、导出和分享；旧版 IndexedDB 录音继续保留并可通过系统窗口导出。
- 不新增教材结构化数据。录音不会自动转写；用户可导出后自行交给 ChatGPT 处理。

第一次点击“开始录音”时请求麦克风权限；Android 13+ 还会请求通知权限。
原生录音为 16 kHz、单声道、16-bit PCM WAV，约 115 MB/小时。
文件逐段写入应用私有目录并约每秒同步；意外关闭后恢复已写入部分，并标记为中断。
存储空间不足或达到单文件 2 GB 上限时停止录音并保留已有内容。
来电、音频焦点丢失或系统静音会暂停录音，需要回到页面检查后继续。
不同厂商的后台限制及真实来电打断仍需实机确认。

覆盖安装且签名一致时可保留学习进度与录音。卸载或清除应用数据前，应先导出需要保留的录音。
此包使用本机 debug 签名，供安装测试；正式上架需维护独立的 release 签名。

## 构建

需要 Android SDK 35、JDK 17、Python 3.11、Node.js 22 和 npm。
从仓库根目录运行：

```powershell
cd app\web
npm ci
cd ..\..\android-app
$env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
.\gradlew.bat assembleDebug
```

Python 默认由 Chaquopy 自动查找；如需指定解释器，可设置环境变量
`BOOK_BUILD_PYTHON` 或使用 `-PbookBuildPython=<python.exe 的完整路径>`。
也可用 Android Studio 打开本目录构建。Linux/macOS 使用 `./gradlew`。

输出为本地调试签名的可安装 APK：

```text
android-app/app/build/outputs/apk/debug/app-debug.apk
```

## 验证

`gradlew.bat assembleDebug lintDebug` 检查 Android 编译和 lint。
在测试模拟器安装并打开 APK 后，从仓库根目录执行：

```powershell
node android-app/tests/smoke_android.cjs emulator-5554
node android-app/tests/smoke_recording_android.cjs emulator-5554
```

该测试通过调试 WebView 操作实际 APK，检查教材库、四种学习模式、来源往返、
Android 返回键、搜索、旋转后输入保留、错误响应和重启后的 SQLite 进度。
测试会在指定模拟器内保存学习记录并重启应用。截图和结果保存于 `.build/android-smoke/`。

录音测试额外检查真实 AudioRecord、快速暂停恢复、锁屏后台、WAV 长度、拖动播放、
归档恢复、系统导出/分享和强制结束进程后的恢复，结果在 `.build/recording-013/`。
仅接受 `emulator-*` 测试设备，不操作连接的实体手机。

浏览器验收使用 Chrome 的合成音频，先启动 API（8000）和 Vite（5173），然后：

```powershell
cd app/web
npm run typecheck
npm test
node smoke-recording.mjs
```

浏览器验收生成 `.build/web-013/test-recording.webm`，供 Android 旧录音导出测试使用，
因此应在原生录音测试前运行。浏览器版本使用 MediaRecorder 和 IndexedDB 分片备份；
应用内部切页不打断录音，但浏览器锁屏/后台持续录音受浏览器限制。

本版验证环境为 Android 15 x86_64 模拟器及 Windows Chrome；尚未做实体手机录音验收。

## Android 实现说明

- Python 在后台初始化，启动前验证教材库和进度数据库；启动失败可点击重试。
- `runtime` 包需通过 Chaquopy `extractPackages` 提取为实体目录，供课程加载器定位资源。
- WebView 与内置 API 共用 `http://127.0.0.1:8765`，保持前端相对 `/api` 路径。
- 学习进度位于应用私有目录 `files/book-data/book-app.sqlite3`，可跨进程重启和覆盖安装保留。
- Android 构建使用独立前端输出目录并禁用 PWA service worker，避免升级后加载旧页面。
- Android 使用纯 Python 的 Pydantic v1；请求字段采用严格文本校验，与桌面 v2 行为一致。
