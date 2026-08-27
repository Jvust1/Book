# Book App 本地运行说明

Phase 1D 是 Book 的第一个可用本地 App MVP：React/Vite PWA 负责界面，FastAPI 负责把现有 Python Runtime 投影成稳定 JSON。教材解析与事实来源仍由 Runtime 负责，前端不会直接读取 `books/`、`courses/`、`library/` 或结构化教材文件。

## 当前能力

- 教材库 → 课程 → Chapter → Section 真实导航。
- Functional Analysis 当前基线：8 Chapter / 132 Section。
- Section 固定提供 `预习｜学习｜复习｜刷题` 四个并列模式，默认 `学习`。
- 模式内容只展示 Runtime 已有的来源对象，不补写不存在的教材内容。
- 点击 `查看教材来源` 可进入结构化来源页，显示纸质教材页、PDF 页、真实锚点（若存在）和上下文。
- 来源页 `返回学习` 会恢复当前会话中的 mode、展开项和滚动位置。
- 中文优先；英文只作为辅助证据显示。
- 浏览器/PWA 可安装，桌面与 390×844 窄屏均有 Chromium 端到端验收。

## 运行边界

当前版本是 **local-first Web/PWA**，不是已经封装好的 Windows 桌面程序：

- FastAPI 与前端都运行在同一台电脑。
- 默认只绑定回环地址 `127.0.0.1`。
- 没有登录、账号、云同步或远程数据库。
- PWA Service Worker 可以缓存前端静态资源，但教材动态数据仍需要本机 FastAPI 运行；因此不要把当前 PWA 描述成“无需后端即可完全离线运行”。
- 当前来源页是结构化教材视图。仓库不包含原始完整 PDF，也没有 Phase 1D PDF Reader；后续可按 canonical `book_id` 接入本地 PDF。
- 当前不生成 AI 教材正文、AI 题目、答案或虚构锚点。

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

保持 Shell A 与 Shell B 正在运行，再开 Shell C：

```powershell
cd app\web
npm run e2e
```

当前验收覆盖两条真实链路：

1. `教材库 → Functional Analysis → Chapter 1 → ch01_s01 → 学习 → 真实教材来源 → 返回学习 → 复习 → 刷题`。
2. 390×844 窄屏下四模式可达，并且页面主体没有横向溢出。

测试会从真实 API payload 读取 source ID、教材页、PDF 页和 anchor 状态，不把测试 fixture 冒充真实教材。

## 开发验证

### Python App/API

仓库根目录：

```powershell
python -m unittest app_tests.test_api app_tests.test_api_live app_tests.test_app_service tests.test_source_resolver -v
```

### Web 单元测试、类型检查与构建

```powershell
cd app\web
npm ci
npm test
npm run typecheck
npm run build
```

Linux CI 的 Chromium 安装使用：

```bash
npx playwright install --with-deps chromium
```

GitHub Actions 中 `.github/workflows/app-ui-tests.yml` 同时验证 App API、Web 单元测试/构建与真实 Chromium acceptance；原有 `.github/workflows/runtime-reference-tests.yml` 仍独立保留，不能用 App UI CI 取代 Runtime readiness gate。

## 本地 API

Phase 1D 只暴露只读接口：

```text
GET /api/health
GET /api/library
GET /api/courses/{course_id}
GET /api/courses/{course_id}/chapters/{chapter_id}
GET /api/courses/{course_id}/sections/{section_id}
GET /api/courses/{course_id}/sections/{section_id}/preview
GET /api/courses/{course_id}/sections/{section_id}/learn
GET /api/courses/{course_id}/sections/{section_id}/review
GET /api/courses/{course_id}/sections/{section_id}/practice
GET /api/courses/{course_id}/sources/{kind}/{source_id}
```

用户可见错误统一为中文 JSON；初始化失败不会在 Python import 阶段直接终止应用。

## 状态保存

Phase 1D 的 Section 返回状态只存在 `sessionStorage`：

```text
book:section-view:{courseId}:{sectionId}:{mode}
```

只保存路由、滚动位置、展开 source IDs 和当前 active source，不保存教材正文。这是当前浏览会话恢复机制，不是长期 `StudyRecord`。

## 当前不在范围内

- 账号 / 云同步
- AI Q&A / AI 生成学习内容
- 本地完整 PDF Reader
- 永久学习进度 / StudyRecord
- 错题数据库
- Chapter Hub
- 课堂录音与字幕
- Windows/Tauri 打包
- 原生移动端

这些能力应在保持现有 Runtime → API → Web 边界的前提下继续扩展，而不是让前端绕过 Runtime 直接读教材资产。
