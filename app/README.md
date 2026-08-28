# Book App 本地运行说明

当前 `feature/study-record-phase-1g` 上的 Book App 已完成 Phase 1G 实现：React/Vite PWA 负责界面，FastAPI 负责把现有 Python Runtime 投影成稳定 JSON，并在服务器侧执行教材搜索、证据选择、教材问答与 StudyRecord 持久化。教材解析与事实来源仍由 Runtime 负责，前端不会直接读取 `books/`、`courses/`、`library/`、结构化教材文件或 SQLite。

> Phase 1G 当前仍在开发分支，尚未合并到 `main`。

## 当前能力

- 教材库 → 课程 → Chapter → Section 真实导航。
- Functional Analysis 当前基线：8 Chapter / 132 Section / 1493 unique search records。
- Section 固定提供 `预习｜学习｜复习｜刷题` 四个并列模式，默认 `学习`。
- 模式内容只展示 Runtime 已有的来源对象，不补写不存在的教材内容。
- 四模式分别保存长期 StudyRecord；首次成功进入为 `in_progress / progress=0`，可手动 `标记完成` 为 `completed / progress=100`。
- 已完成模式重新进入不会倒退；四模式彼此独立。
- StudyRecord 保存在本机 SQLite，页面 reload 后仍可恢复完成状态。
- Course 页面支持教材搜索与整本教材问答；Section 页面支持“问本节内容”。
- Section 问答先限制在当前 Section；本节证据不足时可显式回退到整本教材。
- 生成回答必须携带服务器验证过的真实 citation；点击 citation 可进入现有结构化教材来源页。
- QA → Source → QA 返回时恢复已验证会话，不会为了恢复页面重新调用模型。
- 证据不足时显示稳定资料不足提示，不把模型猜测冒充教材答案。
- 中文优先；英文只作为辅助证据显示。
- 浏览器/PWA 可安装，桌面与 390×844 窄屏均有 Chromium 端到端验收。

## 运行边界

当前版本是 **local-first Web/PWA**，不是已经封装好的 Windows 桌面程序：

- FastAPI 与前端都运行在同一台电脑。
- 默认只绑定回环地址 `127.0.0.1`。
- 当前没有登录、云同步或远程数据库。
- 每台安装生成一个稳定隐藏 UUID `profile_id`；当前 UI 为单用户，不提供账号切换。
- PWA Service Worker 可以缓存前端静态资源，但教材动态数据与 StudyRecord API 仍需要本机 FastAPI 运行；因此不要把当前 PWA 描述成“无需后端即可完全离线运行”。
- 当前来源页是结构化教材视图。仓库不包含原始完整 PDF，也没有本地 PDF Reader；后续可按 canonical `book_id` 接入本地 PDF。
- 教材问答生成文本永远是“模型回答”，不会写回教材结构化正文、搜索索引或 canonical source。
- StudyRecord 只记录个人学习行为，绝不反向修改 canonical 教材资产。
- 真实在线问答需要配置 OpenAI-compatible provider；未配置 provider 时，教材浏览、学习、搜索和本地 StudyRecord 仍可运行，但在线问答不可用。

## StudyRecord 数据边界

本机 SQLite 是长期 StudyRecord authority；浏览器只通过 FastAPI 使用产品接口，不直接访问 SQLite。

逻辑唯一键：

```text
profile_id + course_id + section_id + mode
```

当前持久化语义：

```text
无记录       = 未开始
in_progress   = progress 0
completed     = progress 100
```

- `preview / learn / review / practice` 四模式独立。
- 首次进入一个**已成功加载教材内容**的模式后才 touch StudyRecord。
- 再次进入更新 `last_studied_at`。
- `标记完成` 将该模式设为 completed；重复完成幂等。
- completed 再进入只更新活动时间，不回退完成状态。
- recent learning 按 `last_studied_at` 排序。
- StudyRecord 保存失败时教材内容仍可阅读，界面显示“进度暂未保存”并提供重试。
- repository 初始化失败和运行期 SQLite storage failure 都返回稳定 `study_store_unavailable` 503，响应不暴露数据库路径或内部错误细节。
- 浏览器不能提交 `profile_id` 或 `book_id`；`book_id` 由服务端从 canonical Runtime 解析。
- 浏览器 DTO 不暴露内部 `profile_id / revision / sync_status`。
- Phase 1G 预留 `revision / updated_at / deleted_at / sync_status`，但当前 `sync_status` 固定为 `local`，没有实现 Drive Sync。

数据库位置由 `app/study/paths.py` 统一解析：

```text
BOOK_APP_DATA_DIR=<custom-dir>      -> <custom-dir>/book-app.sqlite3
Windows                            -> %LOCALAPPDATA%/BookApp/book-app.sqlite3
macOS                              -> ~/Library/Application Support/BookApp/book-app.sqlite3
Linux/XDG                          -> ${XDG_DATA_HOME:-~/.local/share}/BookApp/book-app.sqlite3
```

测试/CI 应显式使用临时 `BOOK_APP_DATA_DIR`，避免污染真实本机学习记录。

## 教材问答的数据边界

完整教材数据继续保留在本机 Runtime。一次真实在线问答会先在本机完成确定性检索、Section scope / book fallback 与证据 gate，然后仅把以下内容发送到你配置的在线模型 provider：

- 当前问题；
- 受限的最近对话 history；
- 本次由 Runtime 选出的有界 EvidencePack 片段；
- 当前 course / book / section identity 与允许的回答样式。

不会自动把整个 `books/` 目录或整本教材上传给 provider。`BOOK_QA_API_KEY` 只由 FastAPI 进程读取，不包含在 Web API DTO、浏览器 sessionStorage 或教材 citation 中。

## 环境

推荐：

- Python 3.11–3.13
- Node.js 22
- npm 10+

以下命令均从仓库根目录开始。

## Windows 本地启动

### Shell A：FastAPI

PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r app/api/requirements.txt
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

正常返回：

```json
{"status":"ok"}
```

如需把本地 StudyRecord 存到指定目录，可在启动前设置：

```powershell
$env:BOOK_APP_DATA_DIR="D:\BookAppData"
```

### 配置真实 OpenAI-compatible 问答 Provider

在启动 FastAPI 的同一个 PowerShell 中先设置：

```powershell
$env:BOOK_QA_BASE_URL="https://your-openai-compatible-provider.example/v1"
$env:BOOK_QA_API_KEY="<your-key>"
$env:BOOK_QA_MODEL="<model-name>"
$env:BOOK_QA_TIMEOUT_SECONDS="60"

python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

配置规则：

- `BOOK_QA_BASE_URL`、`BOOK_QA_API_KEY`、`BOOK_QA_MODEL` 必须三者同时存在。
- `BOOK_QA_TIMEOUT_SECONDS` 可省略，默认 `60` 秒，必须为正数。
- 三个必需项全部未配置时，服务使用明确的 unavailable provider；不会偷偷调用外部模型。
- `BOOK_QA_PROVIDER=fake` 只用于确定性测试/CI。设置为其他非空值会被拒绝。
- 不要把真实 Key 写进 `.env.example`、代码、测试 fixture 或提交记录。仓库 `.gitignore` 已忽略 `.env`、`.env.local` 与 `.env.*.local`。

仓库根目录提供 `.env.example` 作为变量名模板，但 FastAPI 本身读取的是进程环境变量；如果你使用自己的 `.env` 加载方式，仍需确保变量最终进入启动 FastAPI 的进程环境。

### Shell B：React/Vite

另开一个 PowerShell：

```powershell
cd app\web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

浏览器打开：

```text
http://127.0.0.1:5173
```

Vite 会把 `/api/*` 代理到本机 `http://127.0.0.1:8000`。

## 真实浏览器验收

首次在当前机器运行 Playwright：

```powershell
cd app\web
npx playwright install chromium
```

为了得到确定、无外部密钥依赖且不会污染真实学习数据的验收结果，测试 API 使用 fake provider 和临时 StudyRecord 目录：

```powershell
$env:BOOK_QA_PROVIDER="fake"
$env:BOOK_APP_DATA_DIR="$env:TEMP\book-app-e2e"
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

保持 FastAPI 与 Vite 正在运行，再开一个 PowerShell：

```powershell
cd app\web
npm run e2e
```

当前 Chromium acceptance 覆盖真实 Functional Analysis Runtime 的主要闭环：教材学习来源往返、英文/中文教材搜索、正常 0 hit、Course 整本问答、Section 本节问答、Section → book fallback、证据不足、QA → Source → QA 零重生成返回、连续追问 history，以及 StudyRecord completion 持久化、reload 恢复、四模式独立、recent learning、内部字段不泄露、Source 往返与 390×844 无 body 横向溢出。

浏览器测试会从真实 API payload 读取 canonical source identity、教材页、PDF 页和 anchor 状态；模型生成部分由 deterministic fake provider 完成，不把测试 fixture 冒充真实教材。

## 开发验证

### Python Runtime

仓库根目录：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python tools/check_runtime_readiness.py books/functional-analysis
```

### Python App/API

```powershell
python -m unittest discover -s app_tests -p "test_*.py" -v
```

### Web 单元测试、类型检查、构建与浏览器验收

```powershell
cd app\web
npm ci
npm test
npm run typecheck
npm run build
npm run e2e
```

Linux CI 的 Chromium 安装使用：

```bash
npx playwright install --with-deps chromium
```

GitHub Actions 中 `.github/workflows/runtime-reference-tests.yml` 保留 Runtime/canonical 参考 gate；`.github/workflows/app-ui-tests.yml` 当前执行全量 Runtime discovery、Functional Analysis readiness、全量 App discovery、Web Vitest/typecheck/build，以及使用临时 SQLite 数据目录和 deterministic fake provider 的真实 Chromium acceptance。

Phase 1G 当前代码 HEAD 验证基线：Runtime 146/146、App 87/87、Functional Analysis readiness `READY`、Web tests/typecheck/build PASS、real Chromium PASS。

## 本地 API

教材 / 搜索 / QA 主要接口：

```text
GET  /api/health
GET  /api/library
GET  /api/courses/{course_id}
GET  /api/courses/{course_id}/chapters/{chapter_id}
GET  /api/courses/{course_id}/sections/{section_id}
GET  /api/courses/{course_id}/sections/{section_id}/preview
GET  /api/courses/{course_id}/sections/{section_id}/learn
GET  /api/courses/{course_id}/sections/{section_id}/review
GET  /api/courses/{course_id}/sections/{section_id}/practice
GET  /api/courses/{course_id}/sources/{kind}/{source_id}
GET  /api/courses/{course_id}/search?q={query}
POST /api/courses/{course_id}/qa
```

StudyRecord 产品接口：

```text
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/touch
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/complete
GET  /api/courses/{course_id}/study-records
GET  /api/study/recent
```

StudyRecord 的两个 POST 接口不接收浏览器身份 request body；`course_id / section_id / mode` 来自路由，canonical `book_id` 与隐藏 `profile_id` 由服务端拥有。

QA request 使用：

```json
{
  "question": "L^p 范数是什么？",
  "section_id": "ch01_s01",
  "history": []
}
```

Course 整本问答时 `section_id` 为 `null`；Section 问答时传真实 Section ID。用户可见错误统一为中文稳定 JSON；教材 Runtime、QA provider 或 StudyRecord repository 初始化失败均不会在 Python import 阶段直接终止应用，相关用户可见错误通过稳定错误契约返回。

## 状态保存

短期浏览会话仍使用彼此独立的 `sessionStorage` namespace：

```text
book:section-view:{courseId}:{sectionId}:{mode}
book:search-view:{courseId}
book:qa-session:{courseId}
```

Section 状态保存 route、scroll、expanded source IDs 与 active source；Search 状态保存 route、query、scroll 与 active source；QA session 保存当前 QA route、已验证的用户/assistant 消息、scroll 与 active citation。QA session 不保存 raw EvidencePack、provider prompt、API Key 或 provider raw response。

这些只是当前浏览会话恢复机制。**长期学习进度由本机 SQLite StudyRecord 保存，二者严格分离。**

## 当前不在范围内

- 账号 / 云同步 / Drive Sync
- 多用户账号切换
- 本地完整 PDF Reader
- 错题数据库
- Chapter Hub
- ExamPoint / Exam Sprint
- Mastery / Next Best Action
- AI 生成教材正文或把 AI 回答写回教材
- AI 生成题 / 变式题
- 课堂录音与字幕
- Windows/Tauri 打包
- 原生移动端 / Android APK
- 同一 Course 多教材正式运行时支持
- Course Compiler / Course Package v2

这些能力应在保持现有 Runtime → API → Web/SQLite 边界的前提下继续扩展，而不是让前端绕过 Runtime 或服务层直接读写 canonical 教材资产。