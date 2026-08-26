# Functional Analysis 中文结构化数据 v0.8

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
- `chunk_007b`：PDF 131-140 / 纸质 112-121，完成 `pv(1/x)`、Theorem 2.1、齐次分布、Proposition 2.2、Theorem 2.3/2.4，并进入 Theorem 2.5 的齐次延拓证明
- `chunk_008a`：PDF 141-150 / 纸质 122-131，完成 Theorem 2.5、Lemma 2.6、Corollary 2.7、基本解、Laplacian/热算子基本解、一般常系数 PDE 基本解，并进入 parametrix
- 中文学习层已同步到 PDF 150
- 搜索索引：GitHub 在 `search_index_v0_7.jsonl` 基线上新增 `search_index_delta_v0_8.jsonl`；Drive 导出包同时包含合并后的 `search_index_v0_8.jsonl`
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，优先保持节/定理/证明语义完整。
- 图像保留原始锚点；本轮 PDF 140 Figure 1 已做视觉核对。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 150
- 对应纸质正文：131
- 下一批：PDF 151-160
- 当前章节：Chapter 3 / 2.5 Parametrices and regularity for elliptic equations
- 当前跨批次对象：parametrix 定义及椭圆正则性证明
