# Book：当代中国经济结构化当前状态

日期：2026-09-23。状态：**源 PDF 首次录入已到末页；全文缺口 remediation 已完成，但 v3 风险驱动复核发现早期 raw OCR 仍存在高风险字符/专名/序号错误，因此 structured review 尚未闭环，不能切换 mygpt。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社，ISBN `978-7-04-051184-0`。
- 源 PDF：255 个物理页；PDF255 为打包元数据页；教材印刷页 1–243。
- 首次物理页覆盖：**PDF1–255**；`source_pdf_end_reached=true`、`ingestion_coverage_complete=true`。
- 本轮新增物理页：**0**；源 PDF 不存在 PDF256。
- 既有 remediation：PDF231–254 完整正文 + PDF181 明显 OCR 破损已解决。
- 当前：`structured_content_complete=true`；但 `targeted_pdf_issues_resolved=false`、`structured_review_complete=false`、`whole_book_complete=false`、`switch_to_mygpt=false`。

## 本轮 v3 风险驱动复核

本轮先读取 `Book_扫描版PDF教材结构化处理提示词.md` v3，按“先审结构化数据 → 风险筛选 → 定点回 PDF”执行：

- PDF1–30：完成版式/已有质量标记复核；直接回原扫描检查 PDF12–15、PDF24–30。
- PDF12/13/24/25：确认并登记 **28 处 source-verified correction**；修正作为独立 correction overlay 保存，不覆盖 raw OCR provenance。
- PDF16–23：既有批次明确记录人工视觉核读/规范化，未发现新的 blocking issue。
- PDF2、5–11：前言/目录等仍有中等优先级 raw OCR source-review debt。
- PDF14–15、26–30：仍有高风险 OCR 需要 source-normalized remediation。
- PDF31–230：对既有 full blocks JSONL 做确定性 OCR 风险筛选，生成定点回源优先级；自动分数只是 triage，不当作“已确认错误”。

代表性直核修正：
- PDF12：`璧如`→`譬如`；`豪赋或要素`→`禀赋或要素`。
- PDF13：`欲坚难填`→`欲壑难填`；`称钠问题`→`稀缺问题`；`马斯治`→`马斯洛`；`萨细尔森`→`萨缪尔森`。
- PDF24：`商唱`→`商品`；`竟争`→`竞争`；`芙代`→`替代`。
- PDF25：`盘利水平`→`盈利水平`；`技术壁急`→`技术壁垒`；枚举恢复为 `①②③④`。

## 本轮成果

GitHub：
- `books/contemporary-china-economy/qc/risk_review_0001_0030_20260923.json`
- `books/contemporary-china-economy/qc/risk_screen_0031_0230_20260923.json`
- `books/contemporary-china-economy/structured/risk_review_corrections_0001_0030_20260923.jsonl`
- `books/contemporary-china-economy/structured/batch_manifest_risk_review_20260923.json`
- 本文件、book manifest 与 economics checkpoint 同步更新。

Drive：
- `Book-Contemporary-China-Economy-Risk-Review-pdf001-230-20260923.zip`
- Drive ID：`1dVIvu3nMDbLP_P_Bij9JOkVDUWoxlafF`
- SHA-256：`3c53164b5fcaf5815f47d08c6e88ac3a375395ec808abf4a93ed4620a3bb4464`
- 大小：`3724685` bytes
- 位置：`Book/03_Exports`
- 新建、未覆盖、未删除历史归档。

## 下一步

执行 `REMEDIATE_RISK_REVIEW_0014_0015_THEN_0026_0030`：先完成 PDF14–15 与 PDF26–30 source-normalized correction；再处理 PDF2/5–11 前置页 OCR debt；随后按 `risk_screen_0031_0230_20260923.json` 高优先级候选做定点回 PDF。最终 structured review/QC/state 闭环之前，不切换 `Jvust2/mygpt`。

> 边界：`full_page_visual_verification=false`。本轮没有把定点源图核验或自动风险筛选冒充全书逐页逐字视觉验收。
