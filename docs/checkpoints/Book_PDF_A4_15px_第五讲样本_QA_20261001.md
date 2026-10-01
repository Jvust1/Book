# Book PDF A4 15px 第五讲同源重排样本 QA

**日期：** 2026-10-01  
**对象：** 《金融经济学十讲》第五讲  
**定位：** 发布门槛验证样本，不替换现有 10px / 12px / 15px 正式产物。

## 本轮实际完成

- 从 `Book_六本教材_LaTeX源码与配图.zip` 中的 `03_金融经济学十讲/chapter_05.tex` 直接重排，不缩放现有 PDF 页面。
- 页面固定为标准 A4：595.28 × 841.89 pt。
- 正文使用真实 15px 口径：11.25 PDF pt/bp；不是把 9pt 页面整体放大。
- 采用 Noto Serif CJK SC 宋体替代；**不是书宋**，因此字体发布门槛仍未通过。
- 将已在 `金融经济学十讲_12px_第五讲原页校勘修正版_v1.pdf` 中核验的来源 PDF 129–130 内容回填进可重排源，覆盖 `fe10-p129-b0570` 至 `fe10-p130-b0585` 的已知污染段。
- 其余来源中仍标为 `C_MACHINE_DRAFT` 的记录原样保留，不把机器草稿冒充已校正文稿。

## QA

- 输出页数：26 页。
- 页面框：全部 A4。
- 正文字号统计主峰：11.25 pt。
- 编译：XeLaTeX 连续两遍成功。
- `Overfull`：0；`BOOK-SCALED-MATH`：0；缺字警告：0。
- 文本边界扫描：0 个文字 span 越出物理页面。
- 已渲染全部 26 页；重点目视核对首页、来源 PDF 129–130 修复段所在页及末页。
- 已确认旧污染标记 `许10`、`FF HATER`、`Pi 及`、`有人限`、`细胜` 均不再出现在样本中。
- 源文件中本轮标记 `A_SOURCE_VERIFIED_20261001` 的记录：16；仍为 `C_MACHINE_DRAFT` 的记录：422。

## Drive 交付

- PDF: https://drive.google.com/file/d/1JaaVPSCnvPOcfhnalN1E9DfonKmxK4jp/view
- QA: https://drive.google.com/file/d/16mS6WkMmmuK8EwTsrF4NmizgcQHhkB9J/view
- 目录: https://drive.google.com/drive/folders/17bUbKi_wR5anBIBmsDJGkq0IcpUGenrv

## 仍未通过

1. 第五讲仍有大量 `C_MACHINE_DRAFT` 源记录；本样本证明 A4 + 真实 15px 的排版路径可行，不代表第五讲内容已逐字校勘完成。
2. 真正书宋字体仍缺可验证的合法字体环境；当前仅用 Noto Serif CJK SC 替代。
3. Preview / Review / Practice 三模式没有统一可编辑源；当前证明的是“教材学习/阅读层”的同源重排链路。
4. 尚未在用户 Windows 阅读器实测适合宽度、适合整页、字体回退与打印表现。

## 文件

- `金融经济学十讲_第五讲_A4_15px_同源重排样本_v1.pdf`
- bytes: 338549
- SHA-256: `faff99f9853816ac0fe55979f0b2209145a5277aa15fddf0f5e27af49f420113`

## 结论

A4 与真实 15px 可以通过**源级重新分页**同时满足，无需扩大纸张，也无需对已有页面做整体缩放。下一步应先把第五讲剩余机器草稿按原扫描逐段校勘，再将同一源生成 10px / 12px / 15px；随后才适合推广到整本及其余五书。
