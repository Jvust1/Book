# Functional Analysis 中文结构化数据 v0.16

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- 已连续结构化 `chunk_001` 至 `chunk_012b`（PDF 1-240）
- `chunk_013a`：PDF 241-250 / 纸质 222-231，完成 Chapter 5 §2.5 Theorem 2.17 多维中心极限定理；完整完成 §2.6 Random walks 与 Theorem 2.18 的低维常返/高维暂留证明；进入 Chapter 5 Exercises 并建立 Exercise 1-21 独立题目节点，其中 Exercise 21(b) 跨到下一批继续
- 中文学习层已同步到 PDF 250
- Figure 4 `The random walk s_n in dimension two` 已视觉核对并保存为导出包图像资产 `figures/fig_ch5_04_random_walk_dimension_two.png`
- PDF 241-250 已逐页视觉抽查；除 Figure 4 外，其余页为正常文字/公式/习题版式
- 搜索索引：新增 `search_index_delta_v0_16.jsonl`；完整导出包包含合并后的 `search_index_v0_16.jsonl`
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

- 已结构化到：PDF 250
- 对应纸质正文：231
- 下一批：PDF 251-260
- 当前章节：Chapter 5 / 3 Exercises
- 当前跨批次对象：Exercise 21(b) 的 q-adic normality 推广（PDF 251 继续）
