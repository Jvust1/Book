# 2026-10-01 · Book 全成果同步

本检查点把当前 GitHub 主线状态和 Drive 阅读成果收拢到一个可恢复入口；不修改 canonical 教材事实，不自动合并 PR。

## GitHub 主线

基线：`2cd209668216bdab77e6a1a3a75146c9b4d963a1`（MinerU ingestion #55）。此前同日已合并 FSRS、sentence-transformers、hybrid retrieval、provenance-safe fuzzy retrieval、FAISS、Docling、MarkItDown fallback 和 Docling-first ingestion。

## Drive 阅读成果

- 六本 10px：6 ×（预习/学习/复习/刷题 PDF + ZIP）= 30 对象。
- 五本 10px r2 修复 QA：20/20 PDF；目标中文说明性小字 <7pt = 0；目标来源/脚注/AI 标签/使用说明等残留 = 0。
- 六本 15px：6 ×（预习/学习/复习/刷题 PDF + ZIP）= 30 对象。
- 总索引：`Book/03_Exports/Book-All-Results-20261001/`。

详细机器清单见 `governance/reading_artifacts_20261001.json`；Drive 同步快照见 `BOOK_ALL_RESULTS_20261001.{md,json}` 与 `FIVE_BOOKS_10PX_R2_FINAL_QA.json`。

## 边界

阅读导出完成不等于 Runtime 自动注册完成；任何后续 App/Runtime 注册仍需以实际代码与测试为准。旧专项 PR #44 / #56 未自动合并。
