# 泛函分析（第2版，江泽坚 / 孙善利）结构化来源快照 V2

本目录登记 Book 对《泛函分析（第2版）》扫描教材的**新增、独立、可追溯**结构化成果。

> 重要：这是新的中文教材来源 `functional_analysis_2e_jiang_sun`，不覆盖仓库中已有的 Stein & Shakarchi `books/functional-analysis/**` 规范教材数据。

## 来源

- 书名：泛函分析
- 版次：第2版
- 作者：江泽坚、孙善利
- 出版社：高等教育出版社
- 来源类型：扫描 PDF
- PDF 页数：247
- 来源 SHA-256：`dcc04c45d761949290f5a35624b8cdf218520a2ceecace7be0017cf013cd19d1`
- 稳定 `book_id`：`functional_analysis_2e_jiang_sun`

## 结构层级

`book -> chapter -> section -> page -> block -> semantic_unit`

V1 先完成：

- 247 个稳定单页 PDF
- 44 个节级 PDF
- 5 个章级 PDF
- `book / chapter / section / page` 元数据

V2 在此基础上增加页内结构：

- 页内 blocks：4877
- semantic units：425
- formula candidates：1494
- 强语义类型：definition / theorem / proposition / corollary / example / proof

## V2 语义统计

| 类型 | 数量 |
| --- | ---: |
| theorem | 110 |
| proof | 137 |
| definition | 79 |
| example | 48 |
| proposition | 45 |
| corollary | 6 |

数学公式本轮只保存 `formula_candidate`、页码锚点、300 dpi 坐标与原图裁剪，不将低质量 OCR 公式静默写成教材事实。

## Drive 成果

父目录：`Book/01_Textbooks/FunctionalAnalysis2_Structured_V2_2026-08-31`

- 完整独立包：`FunctionalAnalysis2_Structured_V2_Complete.zip`
- V2 增量包：`FunctionalAnalysis2_StructureV2_Addon.zip`
- V1 元数据包：`FunctionalAnalysis2_Metadata.zip`
- V1 完整结构包：`FunctionalAnalysis2_Structured_V1.zip`
- 原始来源 PDF：`泛函分析_第2版_江泽坚_孙善利_source.pdf`
- 可读说明：`README.md`

具体 Drive 文件 ID、大小与 SHA-256 见 `artifact_manifest.json`。

## 入库边界

当前成果属于**来源结构化快照**，不是对现有 canonical textbook 的替换。后续若进入 Book Course Package，应新建独立课程/教材实体，再通过 reviewable compiler/validator 流程接入。

推荐稳定主键：

- `book_id`
- `pdf_page`
- `block_id`
- `unit_id`

不要使用 OCR 文本或纸书页码作为唯一主键。
