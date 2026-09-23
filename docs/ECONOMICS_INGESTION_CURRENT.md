# Book：当代中国经济结构化当前状态

更新时间：2026-09-23T02:42:17Z。状态：**源 PDF 首次录入已到末页；PDF12–15 与 PDF24–30 的 HIGH OCR debt 已完成 source-normalized remediation。structured review 仍未闭环，因此暂不切换 Novel。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社，ISBN `978-7-04-051184-0`。
- 源 PDF：255 个物理页；教材印刷页 1–243；首次覆盖仍为 **PDF1–255**。
- `source_pdf_end_reached=true`、`ingestion_coverage_complete=true`、`structured_content_complete=true`。
- 本轮新增物理页：**0**；阶段 B 风险驱动复核按 v3 规范执行。
- 当前 `structured_review_complete=false`、`targeted_pdf_issues_resolved=false`、`whole_book_complete=false`。
- 完成后的项目切换目标已经改为 **`Jvust1/Novel`**；`switch_to_novel=false`，仅在全书最终 review/QC/state closure 后切换。

## 本轮闭环

本轮先重新读取 Drive 根目录 `Book_扫描版PDF教材结构化处理提示词.md`，并按“先审结构化数据 → 风险筛选 → 定点回 PDF → correction overlay”执行。恢复时 GitHub checkpoint 仍把两组 HIGH OCR debt 标为 OPEN；Drive `Book/03_Exports` 中发现一份未登记到当前 GitHub 分支的非重复 remediation 证据归档，因此本轮没有再次制造重复 ZIP，而是重新核验其源 PDF 身份、页图与 correction 内容后同步回权威分支。

- `ECO-QC-OCR-0012-0015`：**RESOLVED_SOURCE_NORMALIZED**。PDF12–15 已全部直接回原扫描；PDF14–15 补齐 meaning-bearing OCR、枚举、公式变量、图注和页首跨页遗漏。
- `ECO-QC-OCR-0024-0030`：**RESOLVED_SOURCE_NORMALIZED**。PDF24–30 已全部直接回原扫描；PDF26–30 补齐 OCR/枚举/标题错误，并恢复 PDF27 一段严重 OCR 乱码。
- 累计 source-verified correction：**111 条**；涉及 PDF 12、13、14、15、24、25、26、27、28、29、30。
- raw OCR 历史不覆盖；修正继续作为独立 correction overlay 保存。
- `full_page_visual_verification=false`：定点回源不冒充全书逐页逐字视觉验收。

## 仍 OPEN

- `ECO-QC-FRONTMATTER-0002-0011`（MEDIUM）：PDF2、5–11；版式/身份已 triage，但字符级 source-normalized review 尚未完成。
- `ECO-QC-REVIEW-0031-0230`：自动风险筛选候选仍须定点回原 PDF；风险分数只是优先级，不是来源错误确认。
- 因仍有上述 review debt，`targeted_pdf_issues_resolved=false`、`structured_review_complete=false`、`whole_book_complete=false`。

## 本轮权威成果

GitHub：
- `books/contemporary-china-economy/qc/risk_review_0001_0030_20260923.json`
- `books/contemporary-china-economy/qc/risk_review_0001_0030_20260923.md`
- `books/contemporary-china-economy/structured/risk_review_corrections_0001_0030_20260923.jsonl`（保留上一层 28 条 correction，不覆盖历史）
- `books/contemporary-china-economy/structured/risk_review_remediation_index_20260923.json`（登记本轮新增 83 条 correction 的页级/类别统计与 Drive 全量记录位置）
- `books/contemporary-china-economy/structured/batch_manifest_risk_review_20260923.json`
- `books/contemporary-china-economy/manifest.json`
- `governance/economics_ingestion_current.json`
- 本文件。

Drive 证据：
- `Book-Contemporary-China-Economy-Risk-Review-Remediation-pdf014-015-026-030-20260923.zip`
- Drive ID：`1_mnPqTL4BbaKbhoN9Anejtc6qrkrnJ2g`
- SHA-256：`73d43bb969477527d1b124c512e6ab82e7e62104b9cc8ad8357e3f8f1af73dca`
- 大小：`2416239` bytes
- 位置：`Book/03_Exports`
- 已存在且内容与本轮源页核验一致，其中内部 `structured/risk_review_corrections_0001_0030_20260923.jsonl` 保存累计 111 条完整 correction 记录，因此**复用而不重复上传**；GitHub 用 remediation index 登记新增 83 条的统计与定位，未覆盖旧 28 条 correction 历史，也未删除任何归档。

## 下一步

执行 `FRONTMATTER_SOURCE_REVIEW_0002_0005_0011_THEN_TARGETED_RISK_SCREEN_0031_0230`：先完成 PDF2、5–11 的字符级 source-normalized review；再按 `risk_screen_0031_0230_20260923.json` 的高优先级候选定点回 PDF。全部 OPEN review debt 闭环并通过 final whole-book structured review/QC/state closure 后，才切换 `Jvust1/Novel`。
