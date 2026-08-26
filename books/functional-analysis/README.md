# Functional Analysis 中文结构化数据 v0.6

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- `chunk_001`：PDF 1-20
- `chunk_002`：PDF 21-40
- `chunk_003a`：PDF 41-50
- `chunk_003b`：PDF 51-60
- `chunk_004a`：PDF 61-70
- `chunk_004b`：PDF 71-80
- `chunk_005a`：PDF 81-90
- `chunk_005b`：PDF 91-100 / 纸质 72-81，极大函数 L^p 定理收尾、分布函数、H^1_r 原子分解、Proposition 5.1、Calderón-Zygmund 分解、dyadic cubes、Lemma 5.2、Figure 7、p-atom 起点
- `chunk_006a`：PDF 101-110 / 纸质 82-91，Corollary 5.3、Theorem 5.4、H^1_r 极大函数、Theorem 6.1、BMO、Theorem 6.2，以及 Exercises 1-10 起点
- 中文学习层已同步到 PDF 110
- 搜索索引：GitHub 继续使用 `search_index_v0_5.jsonl` 作为基线，并新增 `search_index_delta_v0_6.jsonl`；Drive 导出包同时包含合并后的 `search_index_v0_6.jsonl`
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，优先保持节/定理/证明语义完整。
- 图像保留原始锚点；本轮 Figure 7 已视觉核对。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 110
- 对应纸质正文：91
- 下一批：PDF 111-120
- 当前章节：Chapter 2 / 7 Exercises
- 当前跨批次对象：Exercise 10
