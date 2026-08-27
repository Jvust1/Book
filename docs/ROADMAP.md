# Book 开发路线图

> 状态同步：2026-08-27
>
> Stein & Shakarchi《Functional Analysis》已完成全书结构化：`STRUCTURED_COMPLETE` / `RUNTIME_READY`，版本 `v0.36 FINAL`，442 / 442 PDF 页覆盖，最终纸质页 423，全书审计 PASS 20 / WARN 1 / FAIL 0。当前项目主线已从“继续分批结构化第一本书”切换为 Book App 软件能力建设；Phase 1F 教材内问答已完成，下一主线为 Phase 1G 长期学习记录。

## 产品基线

- [x] 一个 Book App 支持多门彼此独立的教材课程
- [x] 当前 App 产品入口：一门 course 恰好对应一本 enabled 主教材
- [x] PDF 页 / 纸质页分离
- [x] 每节固定提供 `预习｜学习｜复习｜刷题` 四个并列入口
- [x] 四模式不强制顺序、不互相锁定
- [x] 教材来源必须可追溯；缺失内容与锚点不得静默编造
- [x] 第一本文档资产完成全书结构化、审计与完成标记
- [ ] 后续加入《实分析》等教材时，作为新的独立 course 注册到 Library

## Phase 1：教材运行时与本地学习 App

### 1A. Runtime 教材导入契约 — 已完成

- [x] 读取 `STRUCTURED_COMPLETE.json`
- [x] 未完成/blocked 教材拒绝进入正式 Runtime
- [x] 读取教材 metadata、PageMap、结构化 chunk、中文学习层与搜索索引
- [x] 校验关键文件、版本、ID 与 canonical identity
- [x] 建立统一 `BookRuntime`
- [x] Functional Analysis 达到 `RUNTIME_READY`

当前真实基线：442 PageMap 行、1493 条唯一搜索记录。

### 1B. Course → Book → Chapter → Section — 已完成

- [x] `CourseRuntime`
- [x] `BookRuntime`
- [x] Chapter 树
- [x] Section 列表
- [x] PDF 页 / 纸质页同时暴露
- [x] Functional Analysis 稳定暴露 8 Chapter / 132 Section

> 底层 `CourseRuntime` 仍保留通用多书兼容能力；当前 App 层只接纳一课程一本 enabled 主教材。

### 1C. Library + Section Learning Runtime — 已完成

- [x] `LibraryRuntime`
- [x] App Library 注册真实课程
- [x] `SectionLearningRuntime`
- [x] Preview / Learn / Review / Practice 四个确定性来源投影
- [x] 四模式自由进入
- [x] review / practice 空结果作为正常状态
- [x] 不把 AI 生成内容冒充教材内容

### 1D. Local-first Book App MVP — 已完成

#### App / API

- [x] `SourceResolver`：object / figure / translation 真实来源解析
- [x] `BookAppService`：Runtime → 稳定 DTO
- [x] FastAPI 本地只读接口
- [x] 用户可见错误使用中文稳定 JSON
- [x] 默认绑定本机 `127.0.0.1`

#### Web / PWA

- [x] React + TypeScript + Vite
- [x] PWA 静态资源支持
- [x] Library → Course → Chapter → Section 真实页面
- [x] Section 默认 `mode=learn`
- [x] `预习｜学习｜复习｜刷题` 四个并列 tab
- [x] 中文优先，英文作为辅助证据
- [x] 缺失中文内容显示明确 fallback，不用英文正文替代
- [x] review 内容默认折叠
- [x] practice 无解析时明确说明教材数据暂未提供

#### 教材来源往返

- [x] 结构化来源页
- [x] 显示纸质教材页 / PDF 页
- [x] 显示真实 `source_anchor`；缺失时明确提示
- [x] 显示来源上下文
- [x] `sessionStorage` 保存当前会话的 route / scroll / expanded IDs / active source
- [x] 从来源返回后恢复 mode、展开状态和滚动位置
- [x] 不把 session 状态伪装成长期 `StudyRecord`

#### 工程质量门

- [x] 固化 `package-lock.json`
- [x] CI 使用 `npm ci`
- [x] Vitest 与 Playwright 测试范围隔离
- [x] TypeScript typecheck
- [x] Vite + PWA build
- [x] Chromium 真实浏览器 acceptance
- [x] 桌面真实来源往返验收
- [x] 390×844 窄屏四模式与横向溢出验收

> 当前 PWA 不是“没有 Python 后端也能完全离线运行”的桌面程序。前端静态资源可缓存，但教材动态数据仍由本机 FastAPI 提供。Phase 1D 也尚未包含完整原始 PDF Reader。

## Phase 1E：教材内搜索与来源跳转 — 已完成

直接复用 Functional Analysis 已存在的 1493 条真实 canonical 索引，不重新发明搜索资产。

- [x] 中文搜索
- [x] 英文搜索
- [x] 术语 / 定理 / 公式 / 例题 / 习题统一命中
- [x] 搜索结果保留 canonical course / book / source identity
- [x] 只为能映射到真实 object / figure 的索引记录生成可跳转结果
- [x] 点击命中项进入结构化教材来源
- [x] 从来源返回搜索上下文
- [x] Search 返回状态与 Section 返回状态分离，并保持 Search 优先匹配当前来源
- [x] `sessionStorage` 只保存 route / query / scroll / active source，不缓存结果 DTO，不冒充长期 `StudyRecord`
- [x] 无结果与索引不可用状态明确区分
- [x] FastAPI 明确区分 200 空结果 / 400 查询错误 / 404 course / 503 search unavailable
- [x] 浏览器端真实搜索 acceptance
- [x] 390×844 搜索与来源往返无 body 横向溢出
- [x] Runtime CI 在 Python 3.11 / 3.12 / 3.13 运行 SearchRuntime gate
- [x] canonical `search_index*.jsonl` 变更会触发 Runtime workflow
- [x] Phase 1E 完成基线：29 个 Vitest 单元测试、TypeScript、PWA build；Chromium acceptance 5 / 5 通过

## Phase 1F：教材内问答 — 已完成

- [x] 问答只使用当前课程允许的真实 canonical 教材资料源
- [x] Course 入口支持整本教材问答
- [x] Section 入口优先当前小节，并在本节证据不足时显式 fallback 到整本教材
- [x] EvidencePack 数量/文本长度有界；最近对话 history 有界，且 history 不作为教材证据
- [x] 服务端证据 gate 先判断是否具备真实可回答内容；模型可做第二次资料不足判断
- [x] 回答必须携带服务端验证过的真实来源引用；未知/伪造 citation fail closed
- [x] 点击 citation 进入现有教材来源页
- [x] QA → Source → QA 返回时恢复同一份已验证会话，不重新调用模型生成原回答
- [x] 连续追问向模型发送当前短期会话 history
- [x] 模型生成回答与教材正文明确区分，不写回教材资产、搜索索引或 canonical source
- [x] 无足够证据时返回稳定资料不足 system notice，不猜测答案
- [x] 服务器侧支持 OpenAI-compatible provider；API Key 不进入浏览器 DTO/sessionStorage
- [x] deterministic fake provider 支持 CI/浏览器验收，不要求外部模型 secret
- [x] 390×844 下 Section QA、citation 来源往返无 body 横向溢出
- [x] Runtime 3.11 / 3.12 / 3.13 Phase 1F contract gate 与全量 `tests` discovery 通过
- [x] Python 3.13 Functional Analysis canonical rebuild/readiness/QA smoke 通过
- [x] 全量 `app_tests` discovery、Web Vitest、TypeScript typecheck、Vite/PWA build 与 Chromium acceptance 通过
- [x] Phase 1F 分支未修改 `books/functional-analysis/**` canonical 教材资产

## Phase 1G：长期学习记录

- [ ] `StudyRecord`
- [ ] 四模式独立进度
- [ ] 最近学习 Course / Section / mode
- [ ] 本地持久化
- [ ] 与当前 `sessionStorage` 短期返回状态分离
- [ ] 后续账号同步接口预留，但本阶段不实现云同步

## Phase 1H：丰富四模式学习体验

当前 Phase 1D 已提供四模式的确定性教材来源投影；以下是更高层学习产品能力，尚未完成。

### 预习

- [ ] 学习目标
- [ ] 前置知识
- [ ] 核心概念
- [ ] 核心公式预览
- [ ] 关键教材图
- [ ] 易卡点
- [ ] 快速检测

### 学习

- [x] 教材真实对象与来源
- [x] 公式 / 结构化对象基础展示
- [ ] 更完整的图表 / 例题交互
- [ ] 个人笔记入口
- [ ] 老师课堂补充入口预留

### 复习

- [x] Runtime 核心对象过滤
- [x] 内容按需展开
- [ ] 1 分钟 / 5 分钟 / 完整复习
- [ ] 闪卡
- [ ] 填空 / 判断 / 简答
- [ ] 公式回忆
- [ ] 错题重做入口

### 刷题

- [x] Runtime 教材 exercise / problem 投影
- [ ] 题目筛选
- [ ] 作答与答案记录
- [ ] 教材变式题接口
- [ ] AI 生成题接口
- [ ] 错题筛选

> 任何新增学习目标、检测题、变式题或 AI 题都必须与“教材原文/教材结构化事实”在数据和 UI 上明确区分。

## Phase 1I：Chapter Hub

- [ ] 章节总结
- [ ] 核心知识点
- [ ] 章节公式
- [ ] 初始考点
- [ ] 可点击思维导图
- [ ] 章节测试

## Phase 1J：ExamPoint 与教材锚点

- [ ] `ExamPoint`
- [ ] `ExamPointAnchor`
- [ ] 考点绑定多个真实教材位置
- [ ] 点击后跳具体来源/锚点
- [ ] 精确高亮（仅在真实几何/anchor 可用时）
- [ ] 一键返回考点
- [ ] 恢复滚动 / 展开 / 筛选状态
- [ ] 上一个 / 下一个考点

> Phase 1D 已完成通用 Section ↔ Source 返回状态机制；Phase 1E 已增加 Search ↔ Source 短期返回状态；Phase 1F 已增加 QA ↔ Source 会话返回状态。本阶段是在同一导航原则上增加 ExamPoint 业务对象，不重复实现另一套导航状态系统。

## Phase 1K：本地 PDF Reader 接入

- [ ] 按 canonical `book_id` 注册本机原始 PDF 路径
- [ ] 不把大体积原始 PDF 提交进 GitHub
- [ ] PDF.js 或等价前端查看器
- [ ] PageMap 驱动 PDF 页 / 纸质页跳转
- [ ] 有真实 anchor geometry 时精确高亮
- [ ] geometry 缺失时只做真实页级定位，不伪造高亮
- [ ] 与现有结构化来源页并存或平滑切换

## Phase 1 首章完整产品验收

Phase 1F 已完成 `ch01_s01` 基础学习、教材搜索和教材问答来源闭环；长期学习记录、ExamPoint 与本地 PDF Reader 仍待后续阶段完成。

- [x] Library → Course → Chapter → Section 导航
- [x] 四学习入口可用
- [x] 纸质页 / PDF 页来源显示
- [x] 结构化来源 → 返回学习闭环
- [x] 窄屏基础可用性
- [ ] 关键图 / 例题 / 习题完整交互验收
- [x] 中英搜索
- [x] 教材内问答返回真实来源
- [ ] 长期学习进度保存与恢复
- [ ] ExamPoint → 教材来源 → 返回考点闭环
- [ ] 本地原始 PDF 页级/锚点级查看

## Phase 2：课堂录音 MVP

- [ ] 开始 / 暂停 / 结束录音
- [ ] Lecture 对象
- [ ] 音频本地持久化
- [ ] 实时语音识别
- [ ] 实时字幕
- [ ] 基础标点与断句
- [ ] 中英文混排
- [ ] 数字 / 百分比
- [ ] 从教材生成专业术语热词

### 快捷标记

- [ ] ⭐ 重点
- [ ] 🎓 考试
- [ ] 📝 作业
- [ ] ❓ 没听懂
- [ ] 💡 拓展

每次点击保存时间戳。

## Phase 3：课堂智能结构化

- [ ] 原始逐字稿
- [ ] AI 精修稿
- [ ] 错别字 / 标点 / 断句修正
- [ ] 口癖 / 重复清理
- [ ] 专业术语规范
- [ ] 精修段落回听原音

### LectureEvent

- [ ] IMPORTANT
- [ ] EXAM
- [ ] HOMEWORK
- [ ] DEADLINE
- [ ] SCOPE
- [ ] GRADE_RULE
- [ ] TEACHER_EXTENSION
- [ ] TEXTBOOK_REFERENCE
- [ ] QUESTION

## Phase 4：考试中心

- [ ] 成绩构成
- [ ] 作业 / 期中 / 期末比例
- [ ] 考试日期与范围
- [ ] 不考 / 必考内容
- [ ] 题型 / 分值
- [ ] 开卷 / 闭卷 / 允许资料
- [ ] 是否提供公式
- [ ] 已确认 / 高概率 / 待确认状态
- [ ] 用户确认 / 修正流程

## Phase 5：教材与课堂融合

- [ ] 老师说纸质页码时通过 PageMap 匹配
- [ ] 识别 Chapter / Section 引用
- [ ] 语义匹配知识点
- [ ] 课堂补充挂到 Concept
- [ ] 老师重点更新考点权重
- [ ] 课堂题进入统一题库

## Phase 6：更多独立课程与教材版本更新

- [ ] 新教材作为独立 course 注册到 Library
- [ ] 复用现有 Runtime / API / Web，不复制应用代码
- [ ] 教材版本差异分析
- [ ] 旧锚点 → 新锚点重映射
- [ ] 历史课堂 / 笔记不失效
- [ ] 如未来确有需求，再设计 App 层多主教材课程，不提前放宽当前产品 gate

## Phase 7：掌握度与自适应复习

- [ ] AnswerRecord
- [ ] Mistake
- [ ] Mastery
- [ ] 错误类型分析
- [ ] 正确率与复习次数
- [ ] 最近复习时间
- [ ] 遗忘管理
- [ ] 间隔复习
- [ ] 考前优先级

## Phase 8：全课程搜索与 AI

- [ ] 搜教材
- [ ] 搜课堂
- [ ] 搜考点
- [ ] 搜题目
- [ ] 搜笔记
- [ ] 搜错题

AI 回答的证据优先级和可用资料源必须显式配置；回答与教材原文在 UI 上保持可区分，并提供可追溯来源。

## 当前单一下一步

**Phase 1G：建立长期 `StudyRecord`，保存最近学习位置与四模式独立进度，并与现有 Section / Search / QA `sessionStorage` 短期返回状态严格分离。**

Phase 1F 的教材问答闭环已经稳定；下一阶段不重新实现搜索/问答，也不把短期会话恢复状态冒充长期学习记录。当前仍不进入课堂录音，也不重复结构化已经完成的 Functional Analysis。