# Functional Analysis 中文结构化数据 v0.2

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 442 页 PDF 的 page label / 纸质页码映射
- 20 页一组的 23 个分卷清单
- 全书目录英中双语结构化
- `chunk_001`：PDF 1-20，前置页、目录、前言、第四卷序言、第一章导言
- `chunk_002`：PDF 21-40 / 纸质 2-21，L^p、Hölder、Minkowski、完备性、L∞、Banach、线性泛函、L^p 对偶、凸集分离、Hahn-Banach 等
- `chunk_003a`：PDF 41-50 / 纸质 22-31，稠密子空间算子延拓、对偶算子、L∞ 对偶、Banach 积分、有限可加测度、复数域修正、C(X) 对偶附录、Theorem 7.1 前半
- 中文学习层已同步到 PDF 50
- 搜索/提问策略已加入：`qa_retrieval_policy.json`

## 关键规则

- 原文与中文学习层分层保存，不覆盖原 PDF。
- PDF 物理页与纸质印刷页分离；`page_map.csv` 是事实源。
- 图像保留原始锚点；公式逐步结构化。
- “预习 / 学习 / 复习 / 刷题”由用户主动选择，不设置流程锁。
- 搜索支持定理编号、中英文术语、别名与语义检索。
- 提问回答必须返回教材来源锚点；未结构化内容只能明确标注后用原 PDF 兜底。
- 整本教材完成后必须执行 `docs/BOOK_COMPLETION_AUDIT.md` 的通篇质量检查，`FAIL=0` 才能标记完成。

## 当前进度

- 已结构化到：PDF 50
- 对应纸质正文：31
- 下一批：PDF 51-60
- 首要任务：完成 Theorem 7.1 唯一性，继续 7.2 The main result 与 7.3 An extension
