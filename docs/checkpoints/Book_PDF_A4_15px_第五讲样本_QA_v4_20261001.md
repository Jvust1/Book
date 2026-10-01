# Book PDF A4 15px 第五讲同源重排样本 QA v4

**日期：** 2026-10-01  
**对象：** 《金融经济学十讲》第五讲  
**范围：** 在 v3 后继续核对原书扫描 PDF 123–124（纸书 104–105）；不覆盖正式 10px / 12px / 15px 产物，不合并 main。

## 本轮完成

- 对照原书扫描完成定理 5.1 陈述与完整证明的源级校勘。
- 升级记录 `fe10-p123-b0432` 到 `fe10-p124-b0452`，共 21 条。
- 恢复 `R_1={r∈M | p(r)=1}`、连续性与渐近无套利的等价命题、正向证明和反向构造证明。
- 原页脚注已经在前一对应正文记录挂接，本轮抑制旧结构化源中的重复副本。
- 定理 5.2 起仍保留 `C_MACHINE_DRAFT`，不宣称已校勘。

## 累计状态

- `A_SOURCE_VERIFIED_20261001`: 95
- `C_MACHINE_DRAFT`: 343
- 已逐页核验原书 PDF 120–124、129–130。

## PDF QA

- 27 页，27/27 标准 A4（595.28 × 841.89 pt）。
- 正文主字号 11.25 pt（15px 口径），源级重新分页，不整体缩放旧 PDF。
- XeLaTeX 两遍通过。
- Overfull 0；BOOK-SCALED-MATH 0；缺字警告 0。
- 1967 个文字 span，越出物理页面 0。
- 定理 5.1 所在输出第 5–6 页通过主渲染器与 Poppler 双重目视检查。
- 旧污染片段 `nA 定理5.1`、`PARA`、`HER BHR`、`旋不连续`、`Van2` 等已从本修复段消失。

## Drive

- v4 PDF: https://drive.google.com/file/d/1ln2yzDczV3Kob69GSh2Prbn7mXTWrauE/view
- v4 QA: https://drive.google.com/file/d/1KSPtprXNj2KHSUKl4C9HLFEdHY1KETNV/view
- 校勘目录: https://drive.google.com/drive/folders/17bUbKi_wR5anBIBmsDJGkq0IcpUGenrv

## 文件哈希

`金融经济学十讲_第五讲_A4_15px_同源重排样本_v4.pdf`

- bytes: 349447
- SHA-256: `fff68174491301f4a3fbdd0a9f58ef48958c3e386ca13ce55b349db03b299a5e`

## 下一步

继续原书 PDF 124 后半页的定理 5.2、式（5.5）与反证法证明，并延伸至 PDF 125。只有逐项对照扫描确认的记录才升级为 `A_SOURCE_VERIFIED_20261001`。
