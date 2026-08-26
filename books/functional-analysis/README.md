# Functional Analysis 中文结构化数据 v0.5

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个存储分卷
- 全书目录英中双语结构化
- `chunk_001`：PDF 1-20，前置页、目录、前言、第四卷序言、第一章导言
- `chunk_002`：PDF 21-40 / 纸质 2-21，L^p、Hölder、Minkowski、完备性、L∞、Banach、线性泛函、L^p 对偶、凸集分离、Hahn-Banach 等
- `chunk_003a`：PDF 41-50 / 纸质 22-31，算子延拓、对偶算子、Banach 积分、有限可加测度、C(X) 对偶、Theorem 7.1 前半
- `chunk_003b`：PDF 51-60 / 纸质 32-41，Theorem 7.1 收尾、Proposition 7.2、Theorem 7.3、Theorem 7.4、Exercises 1-27
- `chunk_004a`：PDF 61-70 / 纸质 42-51，Exercises 27-36、Problems 1-9，并进入第 2 章《调和分析中的 L^p 空间》
- `chunk_004b`：PDF 71-80 / 纸质 52-61，Riesz 插值定理、三线引理、Riesz 图、Hausdorff-Young、Young 卷积不等式，并进入 Hilbert 变换 L^p 理论
- `chunk_005a`：PDF 81-90 / 纸质 62-71，Hilbert 变换 L^2 体系、M. Riesz L^p 有界性定理及证明、极大函数与弱 (1,1) 型估计起点
- 中文学习层已同步到 PDF 90
- 搜索/提问规则：`qa_retrieval_policy.json` + `../../docs/SEARCH_QA.md`
- 全书完成后通篇检查规则：`../../docs/BOOK_COMPLETION_AUDIT.md`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 20 页是存储分卷；实际结构化约 10 页一批，并优先保持节/定理/证明语义完整。
- 图像保留原始锚点；Figure 2–6 已建立锚点，其中 Figure 2–6 的本轮相关页面已做视觉核对。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理/题目编号、中英文术语、别名、公式关键词、页码与语义检索。
- 提问默认依据当前教材，回答必须返回 `source_anchor` 与可跳转教材位置；尚未结构化内容只能明确标注后使用原 PDF 兜底。
- 每本教材全部结构化后必须执行全书质量审计，检查页码、章/节边界、跨批次 continuation、编号、公式、图像、中文术语、重复 ID、空洞页面、搜索命中与来源锚点；只有 `FAIL=0` 才标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 90
- 对应纸质正文：71
- 下一批：PDF 91-100
- 当前章节：Chapter 2 / 4.1 The L^p inequality（跨批次继续）
