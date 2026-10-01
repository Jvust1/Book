# Book PDF A4 15px 第五讲同源重排样本 QA v3

**日期：** 2026-10-01

继续在 `book/pdf-corrections-20261001-v1` 上推进，不改、不合并 `main`。

## 本轮完成

- 对照原书 PDF 122–123（纸书 103–104）。
- 新增 32 条已核验记录：`fe10-p122-b0400` — `fe10-p123-b0431`。
- 第五讲已核验记录累计 74 条；剩余 `C_MACHINE_DRAFT` 364 条。
- 清理了样本第 3–4 页的 CAPM/APT 机器乱码。
- 本轮停在定理 5.1 之前；定理及证明尚未宣称修复。

## v3 QA

- 27 页，全部标准 A4：595.28 × 841.89 pt。
- 正文主字号 11.25 pt（15px 口径）。
- XeLaTeX 两遍成功。
- Overfull 0；BOOK-SCALED-MATH 0；缺字警告 0。
- 文本 span 越页 0。
- 全 27 页渲染检查；第 3–4 页另以 Poppler 复核。
- v1/v2 保留，v3 为独立新文件，不覆盖旧版。

## Drive

- PDF：`金融经济学十讲_第五讲_A4_15px_同源重排样本_v3.pdf`
  - Drive ID：`1J3c4cRUsjG-uDsUWbUc_og74kgRw1rcA`
  - SHA-256：`f3a5acd6c5a00c40a6e5ad47963d4e5d194a1922b3e8e6f082dbfc41d13c08c8`
  - bytes：310085
- QA：`Book_PDF_A4_15px_第五讲样本_QA_v3_20261001.md`
  - Drive ID：`1afD-CL2B9qtV3AHaBCqcEF55L4hW_GB_`

## 仍未通过

1. 定理 5.1 与后续证明仍需从原扫描逐页校勘。
2. 当前中文字体仍为 Noto Serif CJK SC 替代，不是真正书宋。
3. Preview / Review / Practice 尚没有统一可编辑同源排版层。
4. 六书 10px / 12px / 15px 同源生成、全书审校和 Windows 阅读器验收仍未完成。

下一批从 `fe10-p123-b0432` / 定理 5.1 开始。
