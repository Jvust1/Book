# Book：《货币金融学（第三版）》结构化当前状态

- 累计连续处理：**PDF 1–100，共 100 页**；本轮新增 **PDF 51–100，共 50 个新 PDF 页**。
- 正文映射：累计印刷页 **1–94**；下一页为 **PDF 101 / 印刷页 95**。
- 源 PDF：430 页，SHA-256 `3273c38c85ee5f0a6b4a4a74b511e41cda10a51b0160723efdbbf0c72f9ecc73`。
- 本轮 50/50 页完成连续来源读取、结构/版式基础检查；连接器初稿与 PDF51–100 文本层归一化字符序列平均相似度 **0.998741**，最低 **0.991696**。
- 本轮恢复原图：图2-1、图2-2、图3-1～图3-6，共 **8 个编号图像资产**；全部直接从原 PDF 裁切。
- 本轮表格：**表3-1** 已结构化并保存原始扫描截图。
- 本轮公式：**41 条来源公式/表达式**建立 LaTeX visual overlay；**82 个 formula-candidate** 已视觉归类/合并或判定为非公式误报。
- 跨批语义：修复 1 个跨 PDF50→51 的连续段落来源跨度。

## 章节覆盖

- 第2章：本轮补完印刷页45–60（PDF51–66），与上一批合并后来源页覆盖完整。
- 第3章：印刷页61–93（PDF67–99）本轮完成全章来源页覆盖。
- 第4章：已进入印刷页94（PDF100）。

## 完成度边界

全书仍未完成：`whole_book_complete=false`、`structured_review_complete=false`、`switch_to_invest=false`。本轮 `full_page_visual_verification=false`，因为完成的是逐页来源读取 + 版式/高风险对象基础校读，不冒充逐字符视觉验收。

## 下一步

从 **PDF 101 / 印刷页 95** 连续处理下一批 **50 个新 PDF 页**。

## Drive 归档

- `Book-Monetary-Finance-Verified-pdf001-100-20260922.zip`
- Drive ID：`1iC8Z8HiBejLv67-sAzmcPDo5Ncx5lSQ0`
- SHA-256：`1af1edb4d0ad0d58287cc363f01aa7bf1ca7be16b35b59cc7ae2ea606810c212`
- 大小：`5989927` bytes
- 位置：`Book/03_Exports`
- 该包为累计 PDF1–100 归档；GitHub 仅保存状态、批次清单、紧凑页码映射和 QC，避免重复存储大体积 Markdown/JSONL/原图。
