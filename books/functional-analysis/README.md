# Functional Analysis 中文结构化数据 v0.10

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
- `chunk_008b`：PDF 151-160
- `chunk_009a`：PDF 161-170 / 纸质 142-151，完成 Chapter 3 Theorem 3.2 与 Exercises 1-29
- `chunk_009b`：PDF 171-180 / 纸质 152-161，完成 Exercises 29-34、Chapter 3 Problems 1-8，进入 Chapter 4 Baire 纲定理与逐点极限连续性
- `chunk_010a`：PDF 181-190 / 纸质 162-171，完成 Theorem 1.3、处处不可微函数 generic 性、一致有界原理、Fourier 发散，并进入 Theorem 3.1 开映射定理
- 中文学习层已同步到 PDF 190
- Figure 1 `Approximation by P_M` 已视觉核对；稳定教材锚点写入结构数据，图像资产包含在 Drive v0.10 导出包中
- 搜索索引：GitHub 在既有索引上新增 `search_index_delta_v0_10.jsonl`；Drive 导出包包含合并后的 `search_index_v0_10.jsonl`
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，优先保持节/定理/证明/练习语义完整。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 每道 Exercise / Problem 独立建题目节点，星号题保留难度标记；Hint 与题干保持可区分。
- 图像保留稳定锚点；出现教学图时同时在导出包保存可视图像资产并记录 PDF/纸质页。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 190
- 对应纸质正文：171
- 下一批：PDF 191-200
- 当前章节：Chapter 4 / 3 The open mapping theorem
- 当前跨批次对象：Theorem 3.1 的开映射证明
