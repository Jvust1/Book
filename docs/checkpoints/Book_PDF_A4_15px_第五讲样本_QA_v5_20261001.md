# Book PDF A4 15px 第五讲同源重排样本 QA v5

**日期：** 2026-10-01  
**范围：** 原书扫描 PDF 124 后半页至 125（纸书 105–106）；不覆盖正式产物，不合并 main。

## 本轮完成

- 对照原扫描完成定理 5.2、式（5.5）、反证法证明、推论和式（5.7）。
- 升级记录 `fe10-p124-b0453` 到 `fe10-p125-b0501`，共 49 条。
- 恢复 `w_i^n`、`w_k^n`、`w_0^n` 权重定义、组合收益率变形、式（5.6）、方差趋零及矛盾证明。
- 推论后“APT 是否可验证”讨论和式（5.8）起仍保留 `C_MACHINE_DRAFT`。

## 累计状态

- `A_SOURCE_VERIFIED_20261001`: 144
- `C_MACHINE_DRAFT`: 294
- 已逐页核验原书 PDF 120–125、129–130。

## QA

- 27 页，27/27 标准 A4（595.28 × 841.89 pt）。
- 正文主字号 11.25 pt（15px 口径），源级重排，无整页缩放。
- XeLaTeX 两遍通过；Overfull 0；BOOK-SCALED-MATH 0；缺字警告 0。
- 2293 个文字 span，越页 0。
- 输出第 6–8 页经主渲染器与 Poppler 双重检查。
- 本轮目标段旧污染 `lim 93`、`nwo oy`、`RBA K +1`、`wh =—>`、`Dwr;`、`WME n`、`YS wel` 已清除。

## Drive

- v5 PDF: https://drive.google.com/file/d/1hvyRRO5QAeh2r4WvVuGnMUoTxFlRftu5/view
- v5 QA: https://drive.google.com/file/d/1Y2hFCOEgeipxGXo9aYBgml86bZeRmb3_/view
- 校勘目录: https://drive.google.com/drive/folders/17bUbKi_wR5anBIBmsDJGkq0IcpUGenrv

## 文件

`金融经济学十讲_第五讲_A4_15px_同源重排样本_v5.pdf`

- bytes: 351172
- SHA-256: `c45383e8ba21c0b49edf67be74ebea2aeababcb019df119bd26b7f0929535eac`

## 下一步

继续原书 PDF 125 后半页的 APT 可检验性讨论、式（5.8）–（5.12），并延伸到 PDF 126。只有逐项对照扫描确认的记录才升级为 `A_SOURCE_VERIFIED_20261001`。
