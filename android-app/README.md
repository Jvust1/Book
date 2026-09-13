# Book Android APK

Book 学习 0.1.1。适用于 Android 7.0（API 24）及以上的 ARM64 手机和 x86_64 模拟器。
安装包内包含 React 页面、FastAPI、Python Runtime 和 SQLite，无需另开电脑服务器。

教材库、章节浏览、预习/学习/复习/刷题、教材搜索、来源查看和学习进度可离线使用。
本次仅打包仓库已有的泛函分析教材，未增加结构化数据。
安装包未配置问答模型或 API 密钥；问答会显示模型未配置，其他功能可正常使用。

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
```

该测试通过调试 WebView 操作实际 APK，检查教材库、四种学习模式、来源往返、
Android 返回键、搜索、旋转后输入保留、错误响应和重启后的 SQLite 进度。
测试会在指定模拟器内保存学习记录并重启应用。截图和结果保存于 `.build/android-smoke/`。

## Android 实现说明

- Python 在后台初始化，启动前验证教材库和进度数据库；启动失败可点击重试。
- `runtime` 包需通过 Chaquopy `extractPackages` 提取为实体目录，供课程加载器定位资源。
- WebView 与内置 API 共用 `http://127.0.0.1:8765`，保持前端相对 `/api` 路径。
- 学习进度位于应用私有目录 `files/book-data/book-app.sqlite3`，可跨进程重启和覆盖安装保留。
- Android 构建使用独立前端输出目录并禁用 PWA service worker，避免升级后加载旧页面。
- Android 使用纯 Python 的 Pydantic v1；请求字段采用严格文本校验，与桌面 v2 行为一致。
