# Book：《货币金融学（第三版）》结构化当前状态

- 累计连续处理：**PDF 1–300，共 300 页**；本轮新增 **PDF 251–300，共 50 个新 PDF 页**。
- 正文映射：累计印刷页 **1–294**；下一页为 **PDF 301 / 印刷页 295**。
- 源 PDF：430 页，SHA-256 `3273c38c85ee5f0a6b4a4a74b511e41cda10a51b0160723efdbbf0c72f9ecc73`。
- 本轮 50/50 页完成连续来源读取与页面级结构/版式检查；PDF301 仅作为 PDF300 跨批语义边界证据，不计入本轮 50 页。
- 本轮语义块：**623**。
- 本轮图像：恢复 **图8-1《社会总供求与货币供求的关系》** 1 张，直接从原 PDF 裁切，不 AI 重绘。
- 本轮表格：**专栏9-1《2019年12月我国居民消费价格主要数据》**跨 PDF266–267 合并为 1 个完整语义表，保留两页原扫描裁切并结构化。
- 本轮公式：**3 条** source-visual-confirmed LaTeX overlay；**2 个 equation-candidate** 完成视觉归类，其中 `Mds=M` 依据原扫描恢复为 `M_d=M_s`，参考文献片段判定为非公式。
- 本轮新增教材原印数学疑点：**0**；此前 **4 个 OPEN source-typo / math QC** 继续保留，不在 source 层静默改写。
- 跨批语义：PDF250→251、PDF300→301 两处边界均已确认。

## 章节覆盖

- 第8章：印刷页245–253（PDF251–259），补完本章来源页覆盖。
- 第9章：印刷页254–280（PDF260–286），整章来源页覆盖完成。
- 第10章：印刷页281–294（PDF287–300），推进至 10.2.2 附近；下一页继续。

## 完成度边界

全书仍未完成：`whole_book_complete=false`、`structured_review_complete=false`、`switch_to_invest=false`。本轮 `targeted_pdf_issues_resolved_for_batch=true`，但此前 4 个 OPEN source-typo/math QC 仍保留；`full_page_visual_verification=false`，因为本轮是连续来源读取 + 50 页版式检查 + 高风险公式/图表视觉核对，不冒充逐字符人工视觉验收。

## 下一步

从 **PDF 301 / 印刷页 295** 连续处理下一批 **50 个新 PDF 页**。

## Drive 归档

权威累计归档：

- `Book-Monetary-Finance-Verified-pdf001-300-20260923-r2.zip`
- Drive ID：`12uCVuwGqRrc9UtNF-Uw2D4GtUnEkt7yB`
- SHA-256：`36e28a4fdba3ed37cc7ca79f06665274566569ff7e9fe4fd07c4db1a36d87f97`
- 大小：`8538830` bytes
- 位置：`Book/03_Exports`

本轮第一次上传的 `Book-Monetary-Finance-Verified-pdf001-300-20260923.zip`（Drive ID `1Wx1mvD-c23xXzHoNsfndtO9RlcE_HSgN`）正文和批次数据完整，但紧凑页码映射中 PDF260、PDF287 的章节身份受跨页边界继承影响。为避免破坏性覆盖，该对象保留并标记为 **SUPERSEDED**；修正后的 `r2` 为本轮权威归档。
