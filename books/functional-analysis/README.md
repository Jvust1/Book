# Functional Analysis 中文结构化数据 v0.15

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- 已连续结构化 `chunk_001` 至 `chunk_012a`（PDF 1-230）
- `chunk_012b`：PDF 231-240 / 纸质 212-221，完成 Chapter 5 §2.2 martingale 方法（Proposition 2.6、Theorem 2.8、Corollary 2.9、Theorem 2.10）；完成 §2.3 Kolmogorov zero-one law；完成 §2.4 一维 central limit theorem 的 characteristic-function 证明与 weak convergence 表述；进入 §2.5 R^d-valued random variables，并建立多维 CLT 的 Gaussian 极限测度设置
- 中文学习层已同步到 PDF 240
- Figure 3 `The functions φ_ε and ψ_ε in Lemma 2.15` 已视觉核对并保存为 `figures/fig_ch5_03_phi_psi_lemma_2_15.png`
- PDF 231-240 已逐页视觉抽查；除 Figure 3 外，其余页为正常文字/公式版式
- 搜索索引：新增 `search_index_delta_v0_15.jsonl`；导出包包含合并后的 `search_index_v0_15.jsonl`
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

- 已结构化到：PDF 240
- 对应纸质正文：221
- 下一批：PDF 241-250
- 当前章节：Chapter 5 / 2.5 Random variables with values in R^d
- 当前跨批次对象：Theorem 2.17 的正式陈述与证明（PDF 241 开始）
