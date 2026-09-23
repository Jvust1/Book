# Book：当代中国经济结构化当前状态

更新时间：2026-09-23T04:42:37Z。状态：**源 PDF 首次录入已到 PDF255 末页；本轮完成风险筛选前三优先页 PDF169、PDF125、PDF150 的定点回原扫描复核，下一目标推进到 PDF38。structured review 仍未最终闭环，因此暂不切换 Novel。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社，ISBN `978-7-04-051184-0`。
- 源 PDF：255 个物理页；正文印刷页 1–243；首次结构化覆盖 **PDF1–255**。
- `source_pdf_end_reached=true`、`ingestion_coverage_complete=true`、`structured_content_complete=true`。
- 当前处于阶段 B 风险驱动复核；本轮新增物理页 **0**，不再使用“50 个新页”作为成功条件。
- 当前 `structured_review_complete=false`、`targeted_pdf_issues_resolved=false`、`whole_book_complete=false`。
- 完成后的切换目标：**`Jvust1/Novel`**；当前 `switch_to_novel=false`。

## 本轮已闭环：风险优先页 PDF169 / 125 / 150

本轮依据 `risk_screen_0031_0230_20260923.json` 直接回原扫描核验前三个优先候选，并保持 raw OCR 不覆盖、correction overlay 分层：

- **PDF169（印刷页158）**：风险信号被确认。原 OCR 存在大段拉丁乱码、错误枚举符、百分号与法规标题误识别。本轮按原扫描 source-normalized 重建（2）—（7）时间序列条目；其中（7）跨到 PDF170，已把 PDF170 作为必要上下文核到“平滑过渡”为止并合并为单一跨页语义对象。
- **PDF125（印刷页114）**：页面结构完整，但股东大会、董事会、监事会、经理层条目存在系统性枚举 OCR 错误及“盘利→盈利”等意义字符错误；本轮定点修正。
- **PDF150（印刷页139）**：正文连续性完整；修正“几次”“通货膨胀”、`7.47%`、`4.14%`、`信贷资产质押再贷款` 等高价值字符/数字/术语错误。
- 本轮新增 **36 条** source-verified correction records；累计 correction records 从 **111 → 147**。
- PDF170 本轮只作为 PDF169 跨页对象的上下文页，**不**冒充 PDF170 整页候选已闭环。

新增权威成果：

- `books/contemporary-china-economy/structured/targeted_source_corrections_p0125_p0150_p0169_20260923.jsonl`
- `books/contemporary-china-economy/structured/targeted_source_review_p0125_p0150_p0169_20260923.md`
- `books/contemporary-china-economy/qc/targeted_source_review_p0125_p0150_p0169_20260923.json`
- `governance/checkpoints/economics_targeted_source_review_0125_0150_0169_20260923.json`

## 仍 OPEN

`ECO-QC-REVIEW-0031-0230` 仍未整体闭环。前三个候选已完成，剩余当前优先序列：

`38 → 171 → 170 → 226 → 136 → 217 → 216 → 43 → 87`

下一复核页：**PDF38**。

`full_page_visual_verification=false`：当前仅对风险触发页做定点 source review，不冒充整书逐页逐字视觉验收。

## Drive 状态

本轮新增成果均为轻量 GitHub 文本/QC/checkpoint，原扫描 PDF 与既有批次 ZIP 已提供可追溯来源证据，因此不制造新的重复 Drive ZIP。既有 `Book/03_Exports` 批次与复核归档继续保留。

## 完成条件与后继项目

只有剩余 targeted source checks 全部闭环、final whole-book structured review/QC/state closure 通过，并明确写入：

- `whole_book_complete=true`
- `structured_review_complete=true`

之后才停止《当代中国经济》并切换到 **`Jvust1/Novel`**。当前仍不切换。
