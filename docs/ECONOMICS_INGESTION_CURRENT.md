# Book：当代中国经济结构化当前状态

更新时间：2026-09-23T05:55:00Z。状态：**源 PDF 首次录入已到 PDF255；阶段 B 本轮完成此前显式剩余优先候选 PDF226、217、216、43、87 的独立整页回源，优先队列已经清空。现在进入 final whole-book structured review / QC / state closure，尚未达到切换 Novel 的完成门槛。**

## 当前权威进度

- 教材：**《社会主义市场经济理论（第五版）》**，夏永祥、张斌，高等教育出版社。
- 源 PDF：255 个物理页；首次结构化覆盖 **PDF1–255**。
- `source_pdf_end_reached=true`
- `ingestion_coverage_complete=true`
- `structured_content_complete=true`
- `structured_review_complete=false`
- `targeted_pdf_issues_resolved=false`
- `whole_book_complete=false`
- `full_page_visual_verification=false`
- 完成后的后继仓库：**`Jvust1/Novel`**；当前 `switch_to_novel=false`。

## 本轮阶段 B 定点复核

按上一 checkpoint 唯一剩余优先序列完成：

`226 → 217 → 216 → 43 → 87`

直接整页回源页：**PDF226、217、216、43、87**。  
跨页上下文页：PDF225、218、215、44、86、88（只作上下文，不计独立候选闭环）。

本轮新增 **74 条** source-verified correction overlay，累计 **253 条**。典型闭环包括：

- PDF43：恢复 `垄断 / 寡头垄断`、20%/80%、①②③及章节/小节标题；
- PDF87：恢复 `私有制 / 私有性 / 盈亏 / 弊小 / 剥削` 与 ①②③④，清除页眉粘连并核实 PDF86→87→88 跨页语义；
- PDF216：恢复“工业化战略与道路”、工业化模式枚举、马克思引文“肮脏”及脚注；
- PDF217：恢复计划经济工业化模式 ①–⑥、`传入 / 10% / 奠定 / 48.2% / 弊病`；
- PDF226：恢复城市化段落数字/引号/术语与国家统计局脚注 URL。

PDF226 原扫描可见“**50万到20万的城市43个**”。该区间次序从语义上可疑，但来源视觉明确，因此登记 `ECO-SOURCE-ANOMALY-0226-001`，**保留原印刷，不静默猜改**。

## 当前 OPEN

显式优先 source-check 候选：**0**。

仍保留 `ECO-QC-REVIEW-0031-0230`，因为还需要执行最终结构化全量审计，确认：

- correction overlay 与原 blocks 的适用关系；
- 页码/印刷页/章节映射；
- 跨页对象与标题边界；
- 图表引用；
- lower-tier heuristic 候选是否能纯结构化判定为非阻塞，或是否会触发新的定点回源；
- manifest / checkpoint / Current State 一致性。

因此本轮**不**把 `targeted_pdf_issues_resolved`、`structured_review_complete` 或 `whole_book_complete` 提前设为 true。

## Drive

本轮新增成果均为轻量 JSONL / QC / checkpoint / 状态文本，GitHub 已足以长期保存；遵守 artifact dedup，不新建重复 ZIP。原扫描 PDF 与已存在的 verified batch archive 继续作为来源证据。

## 下一步

执行 `FINAL_WHOLE_BOOK_STRUCTURED_REVIEW_QC_STATE_CLOSURE`。只有最终审计通过，并明确写入：

- `whole_book_complete=true`
- `structured_review_complete=true`

之后才停止本教材并切换到 **`Jvust1/Novel`**。
