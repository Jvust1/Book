# Book PDF A4 15px 第五讲同源重排样本 QA v2

**日期：** 2026-10-01

本检查点继续执行 PDF 修复发布门槛验证，不覆盖 v1，不修改或合并 `main`。

## 本轮完成

- 原书扫描 PDF 120–121（纸书 101–102）已人工对照。
- `fe10-p120-b0374` 至 `fe10-p121-b0399` 共 26 条记录升级为 `A_SOURCE_VERIFIED_20261001`。
- 恢复本讲要求、数学预备知识、5.1 节正文、两条脚注与公式 (5.1)–(5.4)。
- 保留 v1 已完成的来源 PDF 129–130 校勘。
- A4 + 真实 15px 继续采用源级流式重排，不缩放旧 PDF 页面。

## v2 QA

- 26 页。
- 全部页面 595.28 × 841.89 pt（A4）。
- 正文主字号 11.25 pt。
- XeLaTeX 两遍成功。
- Overfull 0；BOOK-SCALED-MATH 0；缺字警告 0。
- 文本边界越页 0。
- 全 26 页渲染检查；第 1–2 页另以 Poppler 复核。
- 来源页 120–121 的已知乱码碎片已清除。
- 累计：42 条 `A_SOURCE_VERIFIED_20261001`，396 条 `C_MACHINE_DRAFT`。

## Drive

- PDF：`金融经济学十讲_第五讲_A4_15px_同源重排样本_v2.pdf`
  - Drive ID：`14kpUclw97Zxrq0TIq28bJrtHSAL7bi_A`
  - SHA-256：`4f54c75bd9193ba6de935b27fa8269e2a67ef0984b4d3ff4c04e4702a7cada6a`
  - bytes：344006
- QA：`Book_PDF_A4_15px_第五讲样本_QA_v2_20261001.md`
  - Drive ID：`1c5xwtJmEBe-8MMiMQaQVaQ2Vp1UqVJBJ`

## 未通过的门槛

1. 来源 PDF 122 起仍有大量机器转录错误；样本第 3 页已经能看到，不能宣称第五讲完成。
2. 当前中文字体仍为 Noto Serif CJK SC 替代，不是真正书宋。
3. Preview / Review / Practice 尚没有统一可编辑同源排版层。
4. 六书 10px / 12px / 15px 同源生成、全书内容审校和 Windows 阅读器验收仍未完成。

下一批从来源 PDF 122 起连续校勘，只有和原扫描逐项核对后的记录才升级质量标记。
