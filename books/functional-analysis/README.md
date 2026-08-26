# Functional Analysis 中文结构化数据 v0.31

本目录是 Book Course OS 对 Stein & Shakarchi《Functional Analysis》的持续结构化结果。

## 已完成

- 已连续结构化至 PDF 400 / 纸质正文 381。
- `chunk_020b`：PDF 391-400，完成 Chapter 8 §7.4 dyadic decomposition 的估计 (66)、强几乎正交 (68)-(71)；完整完成 §7.5 Almost-orthogonal sums（Proposition 7.4、(72)）与 §7.6 Theorem 7.1 proof（奇数维 + 偶数维解析插值、(73)-(78)）；进入 §8 Counting lattice points，完成 §8.1 Proposition 8.1 与 (79)-(81)、§8.2 Poisson summation Proposition 8.2 与 (82)-(83)，并进入 Theorem 8.3 的正则化证明。
- 中文学习层已同步到 PDF 400。
- PDF 391-400 已逐页视觉抽查；PDF 397 / 纸质 378 的 Figure 2（The region D~_R）已保存为独立图像资产。
- 搜索索引新增 `search_index_delta_v0_31.jsonl`；完整导出包中的合并 `search_index_v0_31.jsonl` 共 1046 条记录。
- 原文与中文学习层分离；`page_map.csv` 仍为页码事实源；全书完成后仅在审计 FAIL=0 时标记 `STRUCTURED_COMPLETE`。

## 当前进度

- 已结构化到：PDF 400
- 对应纸质正文：381
- 下一批：PDF 401-410
- 当前章节：Chapter 8 / 8 Counting lattice points / 8.2 Poisson summation formula
- 当前跨批次对象：Theorem 8.3 的证明；PDF 400 已完成低频和 `O(R^{1/2}δ^{-1/2})`，PDF 401 将继续高频尾和、夹逼 (84)-(85)、选择 `δ=R^{-1/3}` 完成 `O(R^{2/3})`，随后进入 strongly convex domains 与 §8.3 Hyperbolic measure。
