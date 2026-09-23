# Book：当代中国经济结构化当前状态

更新时间：2026-09-23T05:43:00Z。状态：**源 PDF 首次录入已到 PDF255 末页；本轮继续阶段 B 风险驱动复核，完成 PDF38、PDF136、PDF170、PDF171 的独立整页定点回原扫描，下一目标推进到 PDF226。structured review 仍未最终闭环，因此暂不切换 Novel。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社，ISBN `978-7-04-051184-0`。
- 源 PDF：255 个物理页；正文印刷页 1–243；首次结构化覆盖 **PDF1–255**。
- `source_pdf_end_reached=true`、`ingestion_coverage_complete=true`、`structured_content_complete=true`。
- 当前处于阶段 B 风险驱动复核；本轮新增物理页 **0**，这不是失败，也不再使用“50 个新页”作为成功条件。
- 当前 `structured_review_complete=false`、`targeted_pdf_issues_resolved=false`、`whole_book_complete=false`。
- 完成后的切换目标：**`Jvust1/Novel`**；当前 `switch_to_novel=false`。

## 本轮已闭环：PDF38 / 136 / 170 / 171

依据 `risk_screen_0031_0230_20260923.json` 的剩余优先序列，本轮直接回原扫描完成 4 个候选整页复核；风险分数仅用于排队，不作为错误证据。

- **PDF38（印刷页27）**：修正第二节标题、垄断/储蓄/收入/大萧条等意义字符 OCR，并恢复“凯恩斯的三大心理规律和国家干预政策”的小节结构。PDF39 只用于确认页末跨页句续接，不计为独立候选闭环。
- **PDF136（印刷页125）**：在历史章末 sparse 核对基础上补做整页风险复核，修正股权分置段、枚举、`逐步削弱`、`融资平台`、正文/“重点概念”粘连及第 6 题 `弊端` 等；保留原扫描可见但语感异常的 source wording，不静默改写原书。
- **PDF170（印刷页159）**：此前只作为 PDF169 跨页上下文；本轮首次独立整页闭环。恢复社会保险法跨页条目、①/②枚举、2012/2013 段落、第二节标题及新农保/新农合/优抚安置原文。
- **PDF171（印刷页160）**：修正页眉页码和社会救助/福利高价值术语，核对 `摘帽的右派分子、刑事罪犯家属`、`社会赞助`、`退休金`、`多渠道`、`特殊教育学校`、`过渡性福利措施`，并恢复页末句界。

本轮新增 **32 条** source-verified correction overlay；累计 correction records **179 条**。历史 raw OCR 不覆盖，所有修正继续分层保存。

## 仍 OPEN

`ECO-QC-REVIEW-0031-0230` 仍未整体闭环。当前剩余优先序列：

`226 → 217 → 216 → 43 → 87`

下一复核页：**PDF226**。

`full_page_visual_verification=false`：只对风险触发页做定点 source review，不冒充整书逐页逐字视觉验收。

## Drive 状态

本轮新增成果为轻量 correction/QC/checkpoint/状态文本；原扫描 PDF 与既有 verified batch archive 已足以提供可追溯源证据，因此遵守 artifact dedup 策略，**不制造新的重复 Drive ZIP**。既有 `Book/03_Exports` 批次与复核归档继续保留。

## 完成条件与后继项目

只有剩余 targeted source checks 全部闭环、final whole-book structured review/QC/state closure 通过，并明确写入：

- `whole_book_complete=true`
- `structured_review_complete=true`

之后才停止《当代中国经济》并切换到 **`Jvust1/Novel`**。当前仍不切换。
