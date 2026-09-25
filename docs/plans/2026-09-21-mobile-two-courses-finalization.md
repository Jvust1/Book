# Book 手机版双课程最终化实施计划

Date: 2026-09-21  
Repository: `Jvust2/Book`  
Current recovery branch: `checkpoint/mobile-two-courses-r1-20260921`  
Current recovery PR: #30 (Draft / unmerged)  
Plan status: APPROVED_BY_USER_FOR_IMPLEMENTATION

## 1. 最终目标

完成 Book Android 手机版的双课程正式可用版本：

1. **泛函分析**
   - 主教材：江泽坚、孙善利《泛函分析（第2版）》
2. **偏微分方程**
   - 主教材：《数学物理方程（第四版）》
   - 全 7 章

两门课程均应在同一个 Book Android App 内可进入，并具备：

- 预习
- 学习
- 复习
- 刷题

四个板块。

同时必须满足：

- 教材内容以原始来源为权威，不凭空补造教材事实、公式、图或标准答案；
- 数学公式优先以可读 LaTeX 表达，并保持可追溯的原始 source/page identity；
- 中文正文支持自由字号调节；
- 正文字体目标为书宋；不把系统默认宋体冒充书宋，不在仓库或交付包中擅自分发无授权字体文件；
- Android 手机版优先，Windows 版不作为本阶段阻塞项；
- 最终交付包括可恢复完整源码、构建/测试记录和可安装 APK；实体手机验收完成后才能宣称手机版正式完成。

## 2. 当前可信恢复点

恢复时首先使用：

- `TWO_COURSES_CURRENT.md`
- `docs/checkpoints/2026-09-21-mobile-two-courses-r1.md`
- `governance/source_candidates/mobile-two-courses-r1.json`
- `governance/pending_sync_mobile_two_courses_r1.json`
- `governance/artifact_manifest.json`

当前可恢复源码候选：

- `Book-Mobile-TwoCourses-0.1.5-dev-r1-Source.zip`
- Drive ID: `1LeVVIqmMpYT1X2nXKgYMztL-f8f74pAY`
- SHA-256: `4443b513e700875c5799dac7c12edcc94c084b9bf0e7d9104128a8840e69ac46`

当前只是 **PARTIAL_SOURCE_CANDIDATE**，不是最终版，也没有被旧 0.1.4 APK 的验证证据自动覆盖。

## 3. 内容完成定义

### 3.1 泛函分析

来源：

- 江泽坚、孙善利《泛函分析（第2版）》
- 247 个来源扫描页必须保持可追溯
- 5 章
- 29 个编号教学小节
- 章末习题按来源全部纳入

完成标准：

1. 已有第一章 §1–§2 转录先独立校读。
2. 从 `ch01_s03` 开始，补录剩余 27 个编号教学小节。
3. 补录各章章末习题。
4. 正文、定义、定理、命题、推论、证明、例题、习题及公式均保留来源页锚点。
5. 每一段数学表达：
   - 有可靠公式文本时转换为规范 LaTeX；
   - OCR/视觉结果存在不确定性时保留原始图/页对照和 review 标记；
   - 未经过来源确认的公式不得作为 canonical 教材公式发布。
6. 完成后所有 29 个编号小节均可进入四个学习板块。
7. “内容完整”指教材来源内容覆盖完整，不等于人为制造教材未提供的答案。

### 3.2 偏微分方程

来源：

- 《数学物理方程（第四版）》
- 7 章
- 33 个编号小节 + 7 个章引言
- 当前 reader 数据共 3,449 条 normalized records

完成标准：

1. 保留现有 2,992 条 supplied JSONL 原始记录。
2. 保留第四章 457 个 Markdown/TeX 规范化块并逐项检查结构。
3. 找回或从对应原始来源页恢复当前缺失的 23 幅原图：
   - 第 2 章：1
   - 第 3 章：3
   - 第 5 章：10
   - 第 7 章：9
4. 26 处仅显示层修正的 LaTeX overlay 必须逐一对照来源确认：
   - 原始文本保持不可变 provenance；
   - 只在确认后提升为 reviewed presentation。
5. 所有来源习题组保留完整题干、后续公式/续文和来源位置。
6. 原教材没有可验证标准解答时，明确显示“教材来源未提供可验证解析”，不得补造教材答案。
7. 全 7 章均可进入四个学习板块。

## 4. 四个板块的正式验收标准

### 4.1 预习

每节必须有来源驱动的：

- 本节目录/结构；
- 定义、定理、命题、公式、例题、习题等类型概览；
- 关键 source refs；
- 可进入原文的位置；
- 用户预习笔记。

禁止把模型自己生成、但无法追溯教材的知识点冒充教材内容。

### 4.2 学习

每节必须：

- 按教材顺序提供完整正文；
- LaTeX 数学可离线渲染；
- 图、公式、证明、例题与正文顺序正确；
- 显示来源页/来源记录；
- 可以查看原始扫描页或原始记录进行核对；
- 长公式可横向滚动，不截断公式。

### 4.3 复习

必须采用“先回忆、后核对”的交互：

- source-backed recall prompt；
- 用户先输入或口述自己的复述；
- 再展开教材原文/定义/定理核对；
- 保存本地复习笔记、自评与历史；
- 自评不得冒充客观 mastery 评分。

### 4.4 刷题

必须：

- 纳入来源中全部可识别习题/问题；
- 保持题目续文、公式、图和来源关系；
- 用户答案支持 LaTeX；
- 支持答案公式预览；
- 来源有标准解答时显示并标注来源；
- 来源无标准解答时不得伪造；
- 支持本地答案、自评和历史记录。

## 5. LaTeX、字号与字体

### 5.1 LaTeX

- 数学显示继续采用离线渲染；
- 当前候选的 MathJax SVG 路径可保留，但最终需通过 Android WebView 实机验收；
- 禁止执行不安全 TeX/HTML 扩展；
- 数学字体保持数学排版字体，不强行套中文书宋。

### 5.2 自由字号

正式要求：

- 正文范围至少 12–40 px；
- 1 px 步进；
- 滑块 + 数值输入；
- 设定本地持久化；
- 章节切换、App 重启后保持；
- 公式容器与正文缩放关系需手机端检查，不能出现裁切和溢出。

### 5.3 书宋

- UI 提供“书宋”阅读字体选择。
- 若目标设备没有可确认的书宋字体，则支持用户导入其合法拥有的本地字体文件。
- 字体文件只保存在用户设备，不上传 GitHub/Drive，不随源码或 APK 擅自分发。
- 未导入真实书宋时必须显示 fallback 状态，不得把其他宋体标成“书宋”。

## 6. 应用集成路线

### Phase A — 恢复与冻结 r1

1. 拉取上述 r1 source archive。
2. 校验 SHA-256。
3. 校验 ZIP CRC 与成员 manifest。
4. fresh extraction 后重新运行现有回归。
5. 以该恢复结果为后续 implementation branch 的起点。

### Phase B — 教材数据补齐

优先顺序：

1. 泛函第一章 §1–§2 独立校读；
2. 泛函 `ch01_s03` 起继续逐节补录；
3. 泛函其余章节和章末习题；
4. 偏微分 23 幅缺图恢复；
5. 偏微分 26 处 LaTeX overlay 来源审校；
6. 双课程完整性 gate。

每一个内容对象都必须保留 provenance；不允许因为 UI 需要而虚构缺失教材事实。

### Phase C — 四板块内容完整性

对两门课每一节执行：

- preview coverage
- learn full-source coverage
- review source-backed prompts
- practice source exercise coverage

建立自动化检查，要求：

- 所有教学 section 均存在四模式入口；
- 每个 mode 的 source refs 可闭合到该 section；
- 原文对象不能因为分组而丢失；
- exercise continuation 不被拆断；
- 未解决 gap 明确 fail closed。

### Phase D — 正式 application-code integration

从当前可恢复候选建立新的非默认 implementation branch。

要求：

- 只增量集成 r1 已审阅 App 改动；
- 不覆盖无关历史文件；
- 不改写原 `books/functional-analysis/**` Golden Course；
- 不使用本次任务顺便激活 H3b/B4b/B5/Lecture authority；
- 如果正式接入两门课程必须触发既有 B5 或 StudyRecord book-version migration Human Gate，则先形成独立设计/迁移计划，不静默越过门禁。

### Phase E — Android 前端与阅读体验

完成并验证：

- 双课程 Library 入口；
- 课程/章/节导航；
- 四板块入口；
- LaTeX；
- 扫描页/来源回看；
- 书宋选择/导入；
- 12–40 px 字号；
- 笔记与本地持久化；
- Android 系统导出；
- 横竖屏与 390×844 等手机尺寸；
- Android 返回键、进程重启、旋转、离线状态。

### Phase F — 自动测试与构建

必须运行：

1. Python Runtime/App 全回归；
2. reader/content integrity；
3. 数学片段渲染检查；
4. Web tests；
5. TypeScript typecheck；
6. production web build；
7. Android `assembleDebug`；
8. Android `testDebugUnitTest`；
9. Android `lintDebug`；
10. 模拟器 smoke。

任何失败都保留真实日志，不把 blocked/failed 写成 PASS。

### Phase G — ARM64 实体手机验收

目标：Xiaomi 14 / ARM64。

最低验收：

- 安装/覆盖升级；
- 两门课程全部可进入；
- 随机抽样全部 7+5 章；
- 预习/学习/复习/刷题实际操作；
- LaTeX/长公式；
- 图片；
- 字号调节与重启持久化；
- 用户导入书宋字体并实际应用；
- 笔记保存、恢复；
- 系统文件导出；
- 离线启动；
- Android 返回键/锁屏/后台/恢复；
- 不破坏旧学习数据和录音数据。

真机未通过前，不标记 Android final/stable。

## 7. 最终交付物

最终 Checkpoint 至少包含：

- 完整 Android App 源码 ZIP；
- 可安装 APK；
- 两门课规范化结构化数据包；
- 双课程内容 manifest；
- 完整性/缺口报告；
- 构建日志；
- 自动测试结果；
- Android 模拟器结果；
- ARM64 真机验收记录；
- SHA-256；
- GitHub exact commit / PR；
- Drive artifact IDs。

所有成果进入 `governance/artifact_manifest.json`，重复内容按 SHA-256 复用，不盲目重传。

## 8. 完成门

只有同时满足以下条件才允许称为“手机版双课程最终版”：

- [ ] 泛函 29 个编号教学小节及章末习题来源内容录入完成；
- [ ] 泛函已录入内容完成独立校读；
- [ ] 偏微分 7 章/33 节+引言内容覆盖完整；
- [ ] 偏微分 23 幅缺图已恢复，或明确证明来源本身无法提供并留下不可伪造的缺口状态；
- [ ] 26 处显示层 LaTeX 修正完成来源审校；
- [ ] 两门课每节四板块覆盖通过；
- [ ] 数学渲染检查通过；
- [ ] 自由字号通过 Android 实机验收；
- [ ] 书宋导入/选择通过 Android 实机验收；
- [ ] Python/Web/TypeScript/Android build/lint/unit/smoke 必要 gate 全绿；
- [ ] ARM64 真机验收通过；
- [ ] 最终源码/APK/manifest/验证证据归档并回读；
- [ ] GitHub 当前状态与 Drive artifact manifest 一致。

## 9. 明确非目标 / 安全边界

本计划不自动授权：

- 合并 PR #26 / #28 / #29 / #30；
- 直接写 `main`；
- 删除旧版本、旧教材、历史 artifact、分支或证据；
- force-push / hard reset / history rewrite；
- 无来源补造教材答案、公式、图片或事实；
- 绕过独立 B5 / StudyRecord migration / 其他 Human Gate；
- 上传或分发无授权书宋字体文件。

## 10. 当前唯一下一步

**恢复并验证 r1 source archive 后，从泛函 `ch01_s03` 开始继续来源驱动转录，同时安排 §1–§2 独立校读；不在内容完整 gate 关闭前宣称最终版。**
