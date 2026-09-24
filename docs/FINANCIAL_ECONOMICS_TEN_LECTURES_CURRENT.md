# 《金融经济学十讲》结构化当前状态

- 当前阶段：`STRUCTURED_REVIEW`
- 首次结构化：PDF 1–278 连续覆盖完成；PDF 251–277 对应印刷页 232–258，PDF 278 为来源 PDF provenance 包装页。
- `initial_ingestion_complete = true`
- `whole_book_complete = false`
- `structured_review_complete = false`
- `switch_to_invest = false`
- 最新批次：PDF 251–278，共 28 个新物理页；源 PDF 已到末页。
- 最新 Drive 归档：`Book-Financial-Economics-Ten-Lectures-pdf251-278-20260924.zip`，ID `1gbrdef6aH4U-S5TAREcB7EoUB6B4mBZV`，SHA-256 `0b24bd3e12ea5e5019856da0acfe9d6292293617c30bbb33361940aa9b494762`。
- 本批 PDF251 公式 (10.42)–(10.44) 已从扫描页视觉核对；结语、后记、参考文献的专名/年份/书目信息仍进入风险驱动复核。
- 全书当前 OPEN QC：31 项；均需在 structured review 中按风险排序处理，不能因源页到末页而直接切换 Invest。

## 下一步

执行 v3 风险驱动 structured review：先审计已有结构化数据、批次连续性、页码映射、公式记录与 QC；仅对高风险疑点定点回原 PDF。只有 `whole_book_complete=true` 与 `structured_review_complete=true` 同时成立后才切换 `Invest`。
