# Functional Analysis 中文结构化数据 v0.21

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- 已连续结构化 `chunk_001` 至 `chunk_015a`（PDF 1-290）
- `chunk_015b`：PDF 291-300 / 纸质 272-281，完成 Chapter 6 Exercises 15-21 与 Problems 1-7；正式进入 Chapter 7《A Glimpse into Several Complex Variables》，完成 §1 Elementary properties（Proposition 1.1、Proposition 1.2）并进入 §2 Hartogs’ phenomenon，完成 Theorem 2.1 的陈述与 Lemma 2.2，Theorem 2.1 证明跨批次继续
- 中文学习层已同步到 PDF 300
- Chapter 7 Figure 1 `Õ contains the shaded region` 已视觉核对并保存为 `figures/fig_ch7_01_hartogs_shaded_product.png`
- PDF 291-300 已逐页视觉抽查；除 Chapter 7 Figure 1 外，其余页为正常文字/公式/习题版式
- 搜索索引：新增 `search_index_delta_v0_21.jsonl`；导出包包含合并后的 `search_index_v0_21.jsonl`
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，优先保持节/定理/证明/练习语义完整。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 每道 Exercise / Problem 独立建题目节点；结构化阶段只保存题意/Hint/条件，不擅自把题解写入原题节点。
- 图像保留稳定锚点；出现教学图时同时保存可视图像资产并记录 PDF/纸质页。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 300
- 对应纸质正文：281
- 下一批：PDF 301-310
- 当前章节：Chapter 7 / 2 Hartogs’ phenomenon: an example
- 当前跨批次对象：Theorem 2.1 的证明（PDF 300 已开始，PDF 301 继续）
