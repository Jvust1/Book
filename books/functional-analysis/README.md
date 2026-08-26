# Functional Analysis 中文结构化数据 v0.17

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- 已连续结构化 `chunk_001` 至 `chunk_013a`（PDF 1-250）
- `chunk_013b`：PDF 251-260 / 纸质 232-241，收尾 Chapter 5 Exercises 21(b)-35 与 Problems 1-5；正式进入 Chapter 6《An Introduction to Brownian Motion》，完成导论与 §1 The Framework，建立缩放随机游走 S_t^(N)、Brownian motion B-1/B-2/B-3、canonical path space P、Wiener measure、诱导路径测度 μ_N 与目标 μ_N⇒W；进入 §2 Technical Preliminaries 并定义路径度量 d_n,d
- 中文学习层已同步到 PDF 260
- PDF 251-260 已逐页视觉抽查；本批没有新的独立教学图，Chapter 6 opener 作为章节版式而非教学图处理
- 搜索索引：新增 `search_index_delta_v0_17.jsonl`；导出包包含合并后的 `search_index_v0_17.jsonl`
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

- 已结构化到：PDF 260
- 对应纸质正文：241
- 下一批：PDF 261-270
- 当前章节：Chapter 6 / 2 Technical Preliminaries
- 当前跨批次对象：路径度量 d 的基本性质、Borel/cylindrical sets 与 Lemma 2.1（PDF 261 继续）
