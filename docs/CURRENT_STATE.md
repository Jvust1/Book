## 2026-09-27 学习系统 r2 开发增量

基于 rc5@437cf6ea 的真实七书 Windows 源码实现；版本 `1.0.0-rc6-dev`，尚未构建新的 EXE。

- 精讲 42 主题、128 复习知识点、76 配套题；79 个目录条目有精讲。
- 全部 845 个目录入口形成来源知识树；719 个有可整理记录；并不等于全书知识讲义完成。
- 10 道原书题接入参考解答和方法总结（6 道已有推导重组、4 道新增参考答案）。
- 期末速刷、建议重点、错题循环、章节测试已接入源码；高频无真题证据时不作频次声明。
- 56 个 Node 测试、8 个 Python 内容检查、来源投影完整性通过；1175 原始文件哈希不变；增量恢复 1295 文件校验通过。
- 真实 Chromium/MathJax、Go 构建、Windows 实机和独立学科审核未完成，rc5 历史报告不构成本版通过证据。
- 机器入口 `governance/book_learning_r2_20260927.json`；说明 `docs/BOOK_LEARNING_R2.md`；可恢复增量已存 Drive，回读哈希一致。

## 2026-09-26 六本教材逐章 LaTeX / PDF 交付

- 新成果集：`book-six-textbooks-chapter-latex-20260926`；恢复入口：`governance/book_six_textbooks_chapter_latex_20260926.json`。
- 范围：前六本中文教材，61 个正文章节/讲 + 6 份附属资料，共 67 份 PDF、1,469 页；24,702 条结构化记录全部唯一分配。
- 排版：A4；正文沿用本项目 12px≈9pt 约定；实际中文字体为 `Noto Serif CJK SC`，属于宋体替代，未嵌入真正书宋；LaTeX 源码保留可替换字体设置。
- 验证：67/67 两遍 XeLaTeX 成功，1,469/1,469 页栅格化；文本越出物理页面 0，缺字警告 0，横/纵 overfull 0；8 个 Drive ZIP 全部回读，SHA-256 8/8 匹配。
- Drive：`Book/03_Exports/Book-SixTextbooks-Chapter-LaTeX-20260926`，folder ID `1TxF-jkLN0wRo8z0EKN9aBk2Q0jUgL8yB`。
- 内容边界继承 r3：金融经济学普通 OCR 仍为辅助层；公共财政未核定机器表格不升级为事实；AI/reference derivation 和新编答案未加入；本成果是排印交付，不是新的逐字出版级校勘。
- main 未修改，PR #38 仍 Draft/Open/Unmerged。

## 2026-09-26 Book 七书最终内容质量层 r3 / Windows rc4

- **内容发布阻塞项：0。** 新检查点：`governance/book_final_r3_current.json`；报告：`docs/BOOK_FINAL_CONTENT_REPORT_20260926.md`。
- 公共财政 r2 剩余 66 个表格候选全部收口：7 个来源视觉转录保留为 source-grounded 阅读层；59 个机器布局/单元格草稿降为 `source_image_only_table`。66/66 均不具有自动数值 QA 权限。
- 金融经济学 3,591 条普通 OCR 明确为辅助来源层，只用于检索/定位；原页及 42 条定点修正承担更高来源权威。结构异常扫描 0。
- 两门数学教材发布门为 `PASS_WITH_DERIVED_EXCLUDED`：作者有意省略证明与 AI/reference derivation 不再阻塞结构化发布，但 `whole_book_mathematical_acceptance=false`，AI 推导不冒充教材标准答案。
- r3 自动内容门：38 PASS / 0 FAIL。
- Windows `1.0.0-rc4`：学习状态 29 PASS、Go 15 PASS、race 14 PASS、Chromium 42 PASS、发布安全 UI 4 PASS、最终交付 31 PASS，均 0 FAIL。
- rc4 EXE SHA-256：`4297b2c20c8d5db1ada2adb313f2961d70ad7cdd03b1e5298f3271b44a413983`。
- Drive：`Book/03_Exports/Book-Final-r3-rc4-20260926`（folder `1Esll-k8m1pHzuSRxvREXK4a-meJpTsTQ`）。三个大文件以 64 MiB 分片归档，9 个分片已从 Drive 重新读回，逐片与重组后原文件 SHA-256 全部匹配。
- 仍保留的边界是更高等级学术验收与用户本人 Windows 真机验收；这些不是当前 r6 内容发布 blocker。
- PR #38 保持 Draft/Open/Unmerged；没有修改 main。

## Book Windows rc3 最终交付（2026-09-26 同步）

Book 七书 Windows 学习版已完成 rc3 交付。预习、复习、刷题三板块已补齐到当前可用范围：预习包含每节清单、问题/笔记与来源入口；复习支持来源回忆、自评、到期/薄弱/未自评筛选；刷题支持教材题、来源自测、顺序/随机练习、暂停续练、作答历史与错题重练。生成学习提示保存在独立学习投影，不回写教材原文。

数据范围：7 本教材、26,195 条规范记录、2,343 条来源页映射、1,153 个图像资产；562 个教材题目分组；5,176 个来源回忆/自测组。268 条题干不完整索引仅用于回查，不进入正式作答队列。

测试：JavaScript 学习状态 29 PASS；Go 后端 15 PASS；Go race 子集 14 PASS；Chromium 操作回归 42 PASS；最终交付检查 28 PASS，均 0 FAIL。Windows EXE 为 `Book-1.0.0-rc3-Windows-x64.exe`，195,373,056 bytes，SHA-256 `6a3f6804c0ed4e561f9a714afb73dc0d1149dad77bb327b60b2ea6d4a6008a88`。尚未在用户本人 Windows 设备验收，因此保留 rc3。

Drive 已建立 `Book/03_Exports/Book-Windows-rc3-20260926`（folder ID `1X9s88Z9BYBpxeyJv8iuXr9Vzs9eqZ3d8`）。验证记录、检查报告、使用说明与 SHA256SUMS 已上传并读回。EXE、便携包、源码测试包因单文件上传限制改为 64 MiB 无损分片，保存于 `large-files-split`（folder ID `1Gc2ZYo4d_V4rRHv5r9ol-9bNpm5pzVib`）；9 个分片均已从 Drive 回读，逐片 SHA-256 匹配清单，三组重组后原文件 SHA-256 也全部匹配，故大文件 Drive 归档已闭环。没有修改 main，没有自动合并 PR #38。

内容终验边界不变：公共财政剩余表格候选、金融经济学一般 OCR、数学证明/推导独立终验仍未因 App 打包而自动完成。

## 六本教材结构化数据完善 r2（2026-09-25）

在 r1 已知错误修订之上新增 `book-six-textbooks-enhancement-20260925-r2`。本层覆盖六本中文教材，共 24,702 条记录 / 1,901 个 PDF 页映射；统一生成记录级/页级质量门、23,380 条检索索引和严格 QA 证据模式。它是 r1 的增量文本/质量层，不复制未变化的大批原图，不覆盖 source_text/source_record。

《公共财政概论》新增 5 张高风险数值表逐格回原扫描页重录；连同 r1 的表13-1，共 6 张来源核验数值表。4 张具有明确比率关系的表完成 160 个派生比率复算，全部在教材显示精度舍入范围内。仍有 66 个未回源表格分片候选，明确保持 C_MACHINE_DRAFT / review required。

《金融经济学十讲》在 26 个来源页上完成 42 条记录的定点视觉修正，针对“鞅/鞅测度/鞅性质”等系统 OCR 污染的残留热点已为 0；PDF219 的异常被正确判为 σ-域记号污染而非“鞅”错字。42 条只升级为 targeted-source-corrected，周边 OCR 未被冒充全文验收。

Drive r2 ZIP=`1eKimb6q3BhCIOeTOtThdWSqQZFs35bwG`，SHA-256=`0d8efa419886ee2601a7a15e9470852f03ebd4a744bfa545d43627e57e1ed983`；报告=`1GrX4UWAchfjdFt6nB2FeR0lVzAG5cxTt`。恢复入口：`governance/structured_data_enhancement_r2_current.json`。本次不修改 main、不导入 Runtime、不替换 APK、不自动合并 PR #38。

# Book 当前状态

## 结构化成果当前入口：book-results-sync-20260925

本节是独立数据线的恢复入口，不表示已合并到 main。仓库为 `Jvust2/Book`；修订分支 `fix/structured-data-audit-20260924`，PR #38 保持 Draft / Open / Unmerged。数据修订身份为 `book-structured-repair-20260924-r1`，内容检查点提交为 `54b5ddc0eb5ba9cfaa370233a588614b86fd6c02`。

先读 `governance/structured_data_results_sync_20260925.json`，再读 `governance/structured_data_repair_current.json` 和 `docs/STRUCTURED_DATA_REPAIR_20260924.md`。审计原包、原审计报告和修订交付回执均已登记在 artifact_manifest；完整修订包继续复用 Drive 的八个分片及 v3 清单，禁止重复上传或改写旧证据。

已知错误修订与全文独立验收分开：7 本教材、26,195 条记录、2,343 条页映射属于已交付数据范围；公共财政其他正文/表格、金融经济学其余 OCR、110 份参考推导及数学全书论证仍有独立验收工作。此次同步未重新执行数学/应用测试、未替换 APK、未迁移 Runtime。

下方工程叙述保留原历史日期，不作为本数据线下一步；工程阶段以当前 GitHub 机器状态及各自分支为准。本同步观察到 main 为 `2675d2cecab63b28b6ab81a4554e9b7f010afd72`，未修改 main 或其他开发分支。

更新时间：2026-08-29

> 本文件记录当前有效成果、已确认产品决策和唯一下一步。若与旧聊天、旧 Drive CURRENT 或更早规划冲突，以 `main` 中的本文件、`docs/MASTER_PLAN.md`、`docs/ROADMAP.md`、已批准 Phase Spec/Plan 和最新专项架构文档为准。Foundation A 与 H0/H1/H2/H3a 均已通过独立 PR 合并到 `main`；后续任何新架构阶段仍必须经过独立设计、计划、PR 与 exact-HEAD gate。

## 1. 当前工程状态

- Repository：`Jvust1/Book`
- 稳定集成分支：`main`
- 当前阶段：`FOUNDATION_B_TRANSITION`
- 当前状态：`H3A_MERGED_READY_FOR_H4A`
- 当前 `main`：`3c5585b0c5c27d336473a4dfa59ca675097216fd`
- Phase 1F：已合并到 `main`
- Phase 1G design：`docs/superpowers/specs/2026-08-28-study-record-phase-1g-design.md`
- Phase 1G implementation plan：`docs/superpowers/plans/2026-08-28-study-record-phase-1g.md`
- Phase 1G 业务实现：已完成
- Phase 1G：已通过 PR #11 合并到 `main`
- Phase 1G merge commit：`4b111e4b1ffde86a365aaad2a3164f8aedccc819`
- Phase 1G 合并后验证：`main` Book App UI tests run #194 全绿
- Foundation A design：`docs/superpowers/specs/2026-08-28-foundation-a-course-package-design.md`
- Foundation A implementation plan：`docs/superpowers/plans/2026-08-28-foundation-a-course-package.md`
- Foundation A：`COMPLETE_MERGED`
- Foundation A Tasks 1–10：`COMPLETE`
- Foundation A merged PR：`#13`
- Foundation A reviewed head：`f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- Foundation A merge commit：`82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`
- H0 neutral Book identity：PR `#18`，reviewed head `56c289ccdb5bd692efcbd642dfd9267278f5e5af`，merge `3dcc600c2c8a39e1ffc41c07fbf290adfba5035c`
- H1 internal source provenance：PR `#19`，reviewed head `a225f899fb93faca22c2b1f9ad0c2b1ae2a2fed2`，merge `7e54e87b9674455e9f3d275016313f6c9e2487ac`
- H2 Exact-only shared Retrieval seam：PR `#20`，reviewed head `66ac966c5dfe59ebeea82b168b2ee67fc85f9474`，merge `410cede92bcc0783e4fca9b02faec79e5fe77112`
- H3a deterministic Concept graph contract：PR `#21`，reviewed head `1ed4fc6574417b56b4342ae639f81a69dd842c6b`，merge `f69166568839b7038b0f0472baefcee34299fa17`
- Runtime/App consumer migration：Foundation A 明确不在范围内；H0–H3a 也未做公开多教材迁移

当前跨阶段正式架构文档：

- `docs/MASTER_PLAN.md`
- `docs/ROADMAP.md`
- `docs/DEVELOPMENT_STRATEGY.md`
- `docs/LEARNING_INTELLIGENCE_ARCHITECTURE.md`

### 已批准依赖顺序与当前进度（2026-08-29）

```text
H0 neutral Book identity                         COMPLETE_MERGED
→ H1 internal source provenance                  COMPLETE_MERGED
→ H2 Exact-only shared Retrieval seam            COMPLETE_MERGED
→ H3a Concept/ConceptAlignment contract          COMPLETE_MERGED
→ H4a shadow FTS5/BM25 evaluation                NEXT
→ Phase 1H user-visible slices                   AFTER_H4A
```

这是对历史 Roadmap 执行顺序的已批准依赖例外，不追溯改写历史路线图。`H3b`、`B4b`、`B5` 与 StudyRecord book-version migration 仍需以后分别重新设计批准。H4a 本身也不改变 public Search 的 Exact-only 行为。

## 2. 当前教材 / Runtime 基线

当前 Golden Course：Stein & Shakarchi《Functional Analysis》。

```text
course_id = functional_analysis_course
book_id = stein_shakarchi_functional_analysis_2011
8 Chapters
132 Sections
1493 unique search records
STRUCTURED_COMPLETE / RUNTIME_READY
PDF 442 / 442
final printed page 423
audit PASS 20 / WARN 1 / FAIL 0
```

Phase 1G 产品状态实现和 Foundation A Course Package 实现都没有修改 `books/functional-analysis/**` canonical 教材资产；教材事实层与个人学习状态、生成包输出保持单向边界。H0–H3a 同样没有重写 canonical 教材事实。

这本教材已经被 Foundation A 固化为 Golden Course / Reference Course，用于 Course Package、Runtime、App、搜索、QA、StudyRecord 及后续能力的自动回归基准。

## 3. 已完成产品能力

### Phase 1A–1C

- Runtime 导入契约
- Book / Course / Library Runtime
- Chapter / Section 树
- Preview / Learn / Review / Practice 四模式确定性教材投影
- SourceResolver 基础

### Phase 1D

- Local-first FastAPI + React/TypeScript/Vite PWA
- Library → Course → Chapter → Section
- 四学习模式
- 真实来源页、PDF/printed page identity
- Section → Source → Section 返回状态恢复
- 桌面和移动尺寸浏览器验收

### Phase 1E

- deterministic canonical search
- 中英文术语 / 定理 / 公式 / 例题 / 习题检索
- Search → Source → Search 恢复
- zero-result / query error / unavailable 分离

### Phase 1F

- Course / Section source-grounded textbook QA
- Section-first → book fallback
- server EvidenceGate
- citation verification
- 证据不足 fail closed
- QA → Source → QA 会话恢复
- OpenAI-compatible provider 仅服务端持有 key
- deterministic fake provider 支持 CI

### Phase 1G

- 本机 SQLite durable StudyRecord authority
- 首次初始化生成稳定隐藏 UUID `profile_id`
- 可移植数据库路径；支持 `BOOK_APP_DATA_DIR`
- `preview / learn / review / practice` 四模式独立记录
- 首次进入有效模式：`in_progress / progress=0`
- 再次进入更新 `last_studied_at`
- 手动 `标记完成`：`completed / progress=100`
- completed 再进入不倒退；重复完成幂等
- `last_studied_at` 驱动 recent learning
- 保留 `study_record_id / revision / updated_at / deleted_at / sync_status` 等 sync-ready metadata
- 1G 中 `sync_status=local`
- 服务器从 canonical Runtime 取得 `book_id`；浏览器不能伪造 `profile_id` 或 `book_id`
- 浏览器 StudyRecord DTO 不暴露内部 `profile_id / revision / sync_status`
- Section 页面只有在真实学习模式内容成功加载后才 touch StudyRecord
- StudyRecord 保存失败不阻断教材内容阅读，并提供重试
- repository 初始化失败与运行期 storage failure 都稳定映射为 503，不泄露 SQLite 路径或内部细节
- completion 可跨页面 reload 持久化
- Source → Section 往返继续保持原有 route / scroll / expanded state 恢复
- SQLite read connections 有专门生命周期回归测试

### Foundation A — Course Package v1 基础实现

- Course Package schema：`course_package_v1`
- Package version：`1.0.0`
- canonical roles：`primary / supplementary / reference / translation`
- legacy course manifest normalization
- canonical artifact inventory + SHA-256 + deterministic Book content identity
- deterministic Course Package compiler；同一 source → 相同 `package_identity` 与 bytes
- fail-closed staged validator
- compiler / validator CLI + 稳定 JSON/exit contract
- Functional Analysis Golden Course executable gate
- Golden baseline：8 / 132 / 1493 / 442 / printed 423 PASS
- Golden compile 必须通过独立 validator；canonical tree 前后 byte identity 保持一致
- executable Architecture Fitness Functions
- browser durable-SQLite leakage / compiled absolute path / secret-like field / canonical output boundary / Golden mutation 等当前 Foundation invariants 自动检查
- FAST / PR FULL / manual HEAVY 三层 CI 已接线
- App 仍消费既有 Runtime；Foundation A 未迁移 Runtime/App consumer

### Foundation B transition — H0–H3a

- H0：neutral `BookIdentity` 与 canonical role owner，保持 legacy product behavior
- H1：内部 `SourceIdentity` / provenance seam，冻结公开 Search/Source/QA DTO 与浏览器 persistence shapes
- H2：Search 与 QA evidence candidate retrieval 共用 internal Exact-only Retrieval seam，保持原排名/分数/顺序/错误语义
- H3a：纯 stdlib inert Concept/ConceptAlignment/ConceptGraph v1 contract、JSON Schema、确定性 canonical JSON / cycle diagnostics、repository-bound reference validation
- H3a source-bearing non-main alignment 仍 fail closed；没有真实 Concept dataset，也没有 Search/QA/App/StudyRecord 激活

## 4. Phase 1G API / storage contract

当前 StudyRecord 产品接口：

```text
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/touch
POST /api/courses/{course_id}/sections/{section_id}/study/{mode}/complete
GET  /api/courses/{course_id}/study-records
GET  /api/study/recent
```

逻辑唯一键：

```text
profile_id + course_id + section_id + mode
```

状态只有：

```text
无记录 = 未开始
in_progress = progress 0
completed = progress 100
```

不使用滚动距离或停留时间伪造百分比。

`sessionStorage` 仍只负责短期 Section / Search / QA 返回状态，不能替代 SQLite StudyRecord。

## 5. 最新验证证据

### Phase 1G 集成基线

Phase 1G 已合并到 `main`。merge commit `4b111e4b1ffde86a365aaad2a3164f8aedccc819` 的合并后 GitHub Actions run #194 已通过：

```text
Runtime discovery            146 / 146 PASS
Functional Analysis readiness READY
App discovery                 87 / 87 PASS
Web tests                     PASS
TypeScript typecheck          PASS
Web production build          PASS
real Chromium acceptance      PASS
```

真实浏览器验收覆盖 StudyRecord 首次 touch、completion 跨 reload、四模式独立、`/api/study/recent`、内部身份字段不泄露、Source → Section 往返和 390×844 窄屏无 body 横向溢出。

Python 3.13 暴露的 SQLite connection `ResourceWarning` 已通过 RED → GREEN 生命周期测试修复；repository dependency 初始化失败也有回归测试，稳定映射 `study_store_unavailable` 503 且不泄露 SQLite 路径。目前仍可见 FastAPI/Starlette 自身第三方弃用提示，不属于数据连接泄漏。

### Foundation A 历史 pre-merge 实现证据

以下 Task 8/9 数据保留为 Foundation A 合并前的历史验证证据；Foundation A 最终状态以 PR #13、reviewed head `f1eb4ebd144ccb233e5b8b74e97001af214c60bb` 与 merge commit `82f0cbbcfe5078d304ca7c163b81d4eb01b515f4` 为准。

Task 8 exact-head `116cf4275b8006bc48860943c8e50987547cb5a5`：

```text
Course Package CLI focused   4 / 4 PASS
Python full discovery         192 / 192 PASS
Runtime reference #156        Python 3.11 / 3.12 / 3.13 PASS
Book App UI #212              app-api / web-client / browser PASS
real Chromium                 11 / 11 PASS
Functional Analysis readiness READY
```

Task 9 workflow implementation HEAD `94fee411b5f8d67a5db2ef5779657f39c226c220`：

```text
Course Package FAST #1        PASS
Foundation FAST focused       46 / 46 PASS
Architecture Fitness          PASS
Runtime reference #157        Python 3.11 / 3.12 / 3.13 PASS
Golden compile/validate       PASS on Python 3.13 PR FULL path
Book App UI #213              app-api / web-client / browser PASS
real Chromium                 11 / 11 PASS
```

`course-package-heavy.yml` 已定义为 `workflow_dispatch` 手动门，采用 `/tmp` 隔离副本进行重建/恢复，再对 canonical tree 做只读 readiness / Golden / fitness 验证；没有实际手工运行记录时不得声称 HEAVY 已通过。

从 Foundation A 起点 `a99d4638f959e04e54d91efe0ee0dd9ac50488a6` 到 Task 9 implementation HEAD 的差异审计未出现 `app/**` 源码变更，也未出现 `books/functional-analysis/**` canonical 教材变更。

### H0–H3a 集成证据

```text
H0  PR #18  head 56c289cc...  merge 3dcc600c...
    Course Package FAST #22 / Runtime #185 / Book App UI #241 PASS

H1  PR #19  head a225f899...  merge 7e54e87b...
    Course Package FAST #38 / Runtime #209 / Book App UI #271 PASS

H2  PR #20  head 66ac966c...  merge 410cede9...
    Runtime #220 / Book App UI #287 PASS

H3a PR #21  head 1ed4fc65...  merge f6916656...
    Course Package FAST #45 / Runtime #236 / Foundation B #8 / Book App UI #303 PASS
    Python 3.11 / 3.12 / 3.13, App API, Web tests/typecheck/build, real Chromium PASS
```

H3a 独立复审曾发现两个 blocker；RED checkpoint `2bc7fb6b215b618298e6d860450087a7ef4c67af` 在 Foundation B contract #4 精确失败，最终 HEAD `1ed4fc6574417b56b4342ae639f81a69dd842c6b` 修复后全绿并通过第二轮 review。H3a merge commit 为 `f69166568839b7038b0f0472baefcee34299fa17`；post-H3a governance PR #17 合并后当前 `main` 为 `3c5585b0c5c27d336473a4dfa59ca675097216fd`。

## 6. 当前确认的课程产品模型

Book 的核心单位是 Course。

```text
Course
├── primary textbook
├── supplementary / reference / translation books
├── Chapter / Section reading structure
├── Concept Graph learning structure
├── Lectures
├── Exam model
└── Personal learning state
```

按节：预习 / 学习 / 复习 / 刷题。

按章：核心考点 / 章节总结 / 可点击思维导图 / 章节测试。

按整本/课程：Exam Sprint / 期末速通。

最终原则：**App 通用，教材是数据。** 新课程主要走“上传资料 → Course Compiler/结构化 → readiness → 注册”，不是为每本书重新开发 App。

## 7. 同一课程多教材：已确认方案

如果上传两本泛函分析教材，默认放在同一个 Functional Analysis Course 中，而不是简单创建两个孤立课程，也不把原文融合成一本书。

```text
Course
├── Book A: primary
├── Book B: supplementary / reference
└── Concept Graph
```

每本 Book 保持独立 `book_id / book_version_id / chapter / section / page / source_anchor / proof / notation`。

课程级统一发生在 Concept 层，通过 `ConceptAlignment` 连接：

```text
concept_id
book_id
book_version_id
section_id
source_anchor
relation
confidence
revision
```

第一版仍由 primary book 提供课程 Section 主骨架；辅助教材作为同 Concept/Section 的补充证据源。

同一本教材不同 edition 使用 `logical_book_id + book_version_id + Version Mapping`，新版不能覆盖旧版。

## 8. Foundation A：实现状态

Foundation A 的 Course Package v1 基础实现已经完成 Tasks 1–10，并通过 PR #13 合并到 `main`。

- reviewed head：`f1eb4ebd144ccb233e5b8b74e97001af214c60bb`
- merge commit：`82f0cbbcfe5078d304ca7c163b81d4eb01b515f4`
- canonical `books/functional-analysis/**`：零修改
- Runtime/App consumer migration：仍为 0

Foundation A 已完成：

- Course Package schema/version 与教材角色冻结
- legacy manifest normalization
- artifact/hash/content identity
- deterministic compiler
- fail-closed validator
- compiler/validator CLI
- Functional Analysis Golden Course executable gate
- Architecture Fitness Functions 当前 Foundation 集合
- FAST / PR FULL / manual HEAVY CI 分层
- exact-final-HEAD PR gate 与合并

仍不属于 Foundation A 已实现范围：

```text
上传任意新教材
→ 完整自动结构化
→ validation
→ readiness
→ 自动注册到 Runtime/Library
```

这条通用新教材接入主链路仍是后续 Course Compiler 产品化工作；Foundation A 冻结的是可验证 contract / compiler package boundary / Golden trust root，没有把 Runtime/App consumer 改造成新 package consumer。

## 9. Unified Retrieval：已确认长期搜索架构

现有 Phase 1E deterministic search 保留为 Exact 高可信层。

长期组合：

```text
Query Normalizer
↓
Canonical Exact
+ SQLite FTS5 / BM25
+ Formula
+ Concept
+ Semantic
+ LectureEvent
+ ExamPoint
+ Personal
+ isolated Meeting
↓
RRF / equivalent fusion
↓
source-aware reranking
↓
provenance-preserving hits
```

Search 与 QA 已通过 H2 共用内部 Exact-only Retrieval Engine seam；FTS5/BM25 等扩展尚未公开激活。Meeting retrieval 与 Learning retrieval 授权和索引隔离。

## 10. Concept Graph / Concept 360

Chapter/Section 是阅读骨架，Concept Graph 是知识依赖骨架。

H3a 已完成 inert `Concept / ConceptAlignment / ConceptGraph` v1 contract、Schema 与 repository reference validation；当前没有真实生产 Concept dataset，也没有把 Concept 激活进 Search/QA/App/StudyRecord。

Concept 最终连接主教材、辅助教材、prerequisites、课堂、ExamPoint、Questions/Mistakes 与 Mastery。Concept 360 View 最终展示一个知识点从教材到个人学习状态的完整生命周期，但每条内容保持独立 provenance。

## 11. 课堂录音与教材协同

桌面/PWA 和手机/Android 的业务功能一致，都保留录音能力；只允许因平台权限、后台策略、布局和算力造成实现差异。

```text
Audio
→ VAD / local ASR
→ raw_transcript
→ local_refined
→ Section / Concept matching
→ LectureEvents / pending_ai
```

永久分层：`Textbook fact / Lecture fact / Derived AI fusion`，并保留 `raw_audio / raw_transcript / local_refined / ai_refined`。AI refinement 不覆盖 raw source。

## 12. Exam / Mistake / Mastery / Next Best Action

- ExamPoint 第一版只用真实教材结构化证据计算基础重要度。
- Exam Sprint 按 ExamPoint + 最小 prerequisite closure 组织。
- Exam Digital Twin 后续保存考试日期、范围、分值、题型与可信状态。
- StudyRecord 记录学习行为，不等于真正掌握。
- Mastery 根据复习、刷题、错题、回忆和时间等证据更新。
- Next Best Action 最终输出可解释的下一学习动作，AI 不得无证据直接修改事实或 Mastery。

## 13. 多设备同步

长期：

```text
App(s)
→ Book Sync API
→ owner-controlled Drive
```

每台设备保持自己的 SQLite / profile_id；同步增量 record/event，不共享整个 SQLite。朋友端不持有 owner Drive Token/Google 凭证。

## 14. Private Meeting

Meeting 与 Course/Book/Section 独立，默认私有。可复用 Audio/VAD/ASR/SQLite/profile_id/sync/ProcessingJob，但不参与教材知识融合，不进入 shared Learning feed；Meeting retrieval 与 Learning retrieval 隔离。

## 15. 当前明确未实现

以下均已进入正式计划，但当前不能当作已完成：

- 通用“上传任意教材 → 自动结构化 → validation → readiness → Runtime/Library 注册”的 Course Compiler 产品主链路
- Course Package v2 / 后续 schema evolution 与 migration policy
- 同 Course 多教材 Runtime consumer activation 与真实 ConceptAlignment 数据集
- Architecture Fitness 对 raw audio / transcript / Meeting / ExamPoint / Sync 等未来模块的完整集合
- FTS5/BM25/semantic 等 Retrieval 扩展的公开激活；H2 仅完成 Exact seam，H4a shadow evaluation 尚未实现
- 生产 Minimal Concept Graph dataset / Concept 360 UI；H3a 仅完成 inert contract/reference validation
- Chapter Hub / 思维导图
- ExamPoint / Exam Sprint / Exam Digital Twin
- 录音 UI / VAD / ASR / LectureEvent
- Drive Sync / SyncEvent / SyncEngine
- GPT Processing pipeline 真实写回
- Course Timeline / What Changed
- Mistake / Mastery / Next Best Action
- Meeting UI / storage
- Android APK
- raw PDF Reader

## 16. 当前唯一下一步

H0 → H1 → H2 → H3a 已完成并合并。下一实现阶段是 **H4a shadow FTS5/BM25 evaluation**。PR #17 已集成，现仅作为历史治理证据，不再构成新的前置开发阶段。

1. H4a 只做 shadow evaluation：构建/比较 FTS5/BM25 候选与现有 Exact baseline，不改变 public Search/QA 排名与返回行为。
2. H4a 必须定义确定性 query/dataset、覆盖率/排名比较指标、provenance 校验、失败语义与 exact-HEAD regression evidence。
3. H4a 应复用 H2 shared Retrieval boundary，不绕过现有 Exact baseline 或来源身份链路。
4. 不修改 `books/functional-analysis/**` canonical 教材事实。
5. 使用非默认分支、TDD、reviewable PR、exact-HEAD verification；具体 PR 合并仍需用户明确指向该 PR 授权。
6. `H3b`、`B4b`、`B5`、StudyRecord book-version migration 不在本轮批准范围内。

当前不提前实现录音、Drive Sync、Meeting、ExamPoint、Mastery 或 Next Best Action。
