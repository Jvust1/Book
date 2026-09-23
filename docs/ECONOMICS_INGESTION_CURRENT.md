# Book：当代中国经济结构化当前状态

更新时间：2026-09-23T03:27:00Z。状态：**源 PDF 首次录入已到 PDF255 末页；PDF2–11 前置页 source review 已闭环；当前只剩 PDF31–230 风险筛选候选的定点回源复核。structured review 尚未最终闭环，因此暂不切换 Novel。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社，ISBN `978-7-04-051184-0`。
- 源 PDF：255 个物理页；正文印刷页 1–243；首次结构化覆盖 **PDF1–255**。
- `source_pdf_end_reached=true`、`ingestion_coverage_complete=true`、`structured_content_complete=true`。
- 本轮新增物理页：**0**；处于阶段 B 风险驱动复核，不再用“50 个新页”作为成功条件。
- 当前 `structured_review_complete=false`、`targeted_pdf_issues_resolved=false`、`whole_book_complete=false`。
- 完成后的切换目标：**`Jvust1/Novel`**；当前 `switch_to_novel=false`。

## 本轮已闭环：前置页 PDF2–11

本轮直接回原扫描核验 PDF2–11，并新增 source-normalized 前置页记录：

- PDF2：出版社“高等学校经济与管理类核心课程教材”同系列书目广告。核实本书条目、主编、ISBN `978-7-04-051184-0` 和定价 35.00 元。其余广告书目属于非教材正文，原扫描完整保留，分类为 `NON_BLOCKING_SOURCE_RETAINED`，不再作为教材正文债务。
- PDF3：扉页，确认“十二五”江苏省高等学校重点教材、第五版、主编夏永祥/张斌、高等教育出版社。
- PDF4：内容提要、CIP 与版权页，确认 2019 年 1 月第 5 版、CIP 核字（2019）第000791号等关键书目信息。
- PDF5：`郑重声明` source-normalized。
- PDF6–7：`第五版前言` source-normalized，落款“编者 / 2019年1月”。
- PDF8–9：`第一版前言` source-normalized，落款“编者 / 2001年12月于苏州大学”。
- PDF10–11：两页目录 source-normalized；目录确认 11 章、参考文献起始印刷页 241；PDF12 对应正文印刷页 1。

`ECO-QC-FRONTMATTER-0002-0011`：**RESOLVED_SOURCE_NORMALIZED**。

保留信息性非阻塞项：`ECO-QC-FRONTMATTER-CATALOG-0002`，仅说明 PDF2 的完整出版社广告清单保留在原扫描，没有伪装成教材正文。

本轮新增权威成果：

- `books/contemporary-china-economy/structured/frontmatter_source_normalized_0002_0011_20260923.md`
- `books/contemporary-china-economy/qc/frontmatter_review_0002_0011_20260923.json`
- `governance/checkpoints/economics_frontmatter_review_20260923.json`
- 更新 `books/contemporary-china-economy/manifest.json`
- 更新 `governance/economics_ingestion_current.json`
- 更新本文件。

## 已闭环的其它主要问题

- `ECO-QC-FULLTEXT-0231-0254`：RESOLVED。
- `ECO-QC-OCR-0181`：RESOLVED。
- `ECO-QC-OCR-0012-0015`：RESOLVED_SOURCE_NORMALIZED。
- `ECO-QC-OCR-0024-0030`：RESOLVED_SOURCE_NORMALIZED。
- 累计 source-verified correction 仍为 **111 条**，raw OCR 历史不覆盖，correction overlay 保持分层。

## 仍 OPEN

仅剩 `ECO-QC-REVIEW-0031-0230`：自动风险筛选候选需要按优先级定点回原 PDF。风险分数只是检查优先级，不代表来源错误已经成立。

下一优先序列：

`169 → 125 → 150 → 38 → 171 → 170 → 226 → 136 → 217 → 216 → 43 → 87`

下一复核页：**PDF169**。

`full_page_visual_verification=false`：本轮只完成前置页定点回源，不冒充全书逐页逐字视觉验收。

## Drive 状态

本轮前置页记录均为轻量 GitHub 文本/QC/checkpoint，不制造新的重复 ZIP。既有长期/大文件证据继续保留在 `Book/03_Exports`；后续只有产生新的不可替代大文件或长期证据时才新增/更新 Drive 归档。

## 完成条件与后继项目

只有 PDF31–230 targeted source checks 全部闭环、final whole-book structured review/QC/state closure 通过，并明确写入：

- `whole_book_complete=true`
- `structured_review_complete=true`

之后才停止《当代中国经济》并切换到 **`Jvust1/Novel`**。当前仍不切换。
