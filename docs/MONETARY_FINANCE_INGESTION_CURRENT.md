# Book：《货币金融学（第三版）》结构化当前状态

- 累计连续处理：**PDF 1–150，共 150 页**；本轮新增 **PDF 101–150，共 50 个新 PDF 页**。
- 正文映射：累计印刷页 **1–144**；下一页为 **PDF 151 / 印刷页 145**。
- 源 PDF：430 页，SHA-256 `3273c38c85ee5f0a6b4a4a74b511e41cda10a51b0160723efdbbf0c72f9ecc73`。
- 本轮 50/50 页完成连续来源读取与版式基础检查；连接器初稿与 PDF101–150 文本层归一化字符序列平均相似度 **0.998696**，最低 **0.992462**。
- 本轮恢复原图：**图5-1 银行同业拆借业务流程**，以及未编号统计图 **国库券利率及通货膨胀率（1973年1月至2010年1月）**；全部直接从原 PDF 裁切。
- 本轮表格：印刷页120“**3月美股三大指数收盘涨跌数据**”已结构化并保存原始扫描截图。
- 本轮公式：**13 条来源公式/表达式**建立 LaTeX visual overlay；**26 个 formula-candidate** 已视觉归类/合并或判定为非公式误报。
- QC：PDF125 / 印刷页119 的平均收益率示例原印为 `(60+8.89)/9×100%=7.65%`，扫描清晰但数学不自洽；忠实保留原印并标记为疑似教材原印错误，未擅自改写。

## 章节覆盖

- 第4章：本轮补完印刷页95–115（PDF101–121），与上一批合并后来源页覆盖完整。
- 第5章：本轮覆盖印刷页116–144（PDF122–150），推进至 5.5.1。

## 完成度边界

全书仍未完成：`whole_book_complete=false`、`structured_review_complete=false`、`switch_to_invest=false`。本轮 `full_page_visual_verification=false`，因为完成的是逐页来源读取 + 版式/高风险对象基础校读，不冒充逐字符视觉验收。由于存在 1 个教材原印疑似错误的开放 QC 项，本批 `targeted_pdf_issues_resolved_for_batch=false`。

## 下一步

从 **PDF 151 / 印刷页 145** 连续处理下一批 **50 个新 PDF 页**。

## Drive 归档

- `Book-Monetary-Finance-Verified-pdf001-150-20260922.zip`
- Drive ID：`1rH0yjF1Brkc2lHmZFSwSfmt0SuLn9biE`
- SHA-256：`554ceee517918631a2b2cac6e76828927febbdb614923ec68a8540dcd3eaf3b1`
- 大小：`6995094` bytes
- 位置：`Book/03_Exports`
- 该包为累计 PDF1–150 归档；GitHub 继续只保存状态、批次清单、紧凑页码映射和 QC，避免重复存储大体积 Markdown/JSONL/原图。
