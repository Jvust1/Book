# Functional Analysis 中文结构化数据 v0.9

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
- `chunk_005b`：PDF 91-100
- `chunk_006a`：PDF 101-110
- `chunk_006b`：PDF 111-120
- `chunk_007a`：PDF 121-130
- `chunk_007b`：PDF 131-140
- `chunk_008a`：PDF 141-150
- `chunk_008b`：PDF 151-160 / 纸质 132-141，完成 Theorem 2.12、Corollary 2.13、Theorem 2.14、Calderón–Zygmund 定义与 Proposition 3.1，并推进 Theorem 3.2 的前三步及 Lemma 3.3
- `chunk_009a`：PDF 161-170 / 纸质 142-151，完成 Theorem 3.2 的弱 (1,1) 与完整 L^p 证明，并结构化 Chapter 3 Exercises 1-29
- 中文学习层已同步到 PDF 170
- 搜索索引：GitHub 在既有索引上新增 `search_index_delta_v0_9.jsonl`；Drive 导出包包含合并后的 `search_index_v0_9.jsonl`
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，优先保持节/定理/证明/练习语义完整。
- PDF 151-170 以公式、证明和练习为主，视觉抽查未发现需要单独提取的新教学图。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 每道 Exercise 独立建题目节点，Hint 与题干保持可区分；跨页练习不在 chunk 边界截断。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 170
- 对应纸质正文：151
- 下一批：PDF 171-180
- 当前章节：Chapter 3 / 4 Exercises
- 当前跨批次对象：Exercise 29 的提示；随后 Exercises 30-34 与 Problems
