# Book 七书内容最终质量层 r3 — 完成报告

日期：2026-09-26  
质量层：`book-seven-textbooks-release-safety-20260926-r3`  
父层：`book-six-textbooks-enhancement-20260925-r2` + `book-structured-repair-20260924-r1`

## 结论

按 Book r6 已冻结的完成口径，本轮关闭此前登记的三个阻塞型内容待办：公共财政 66 个未核定表格候选、金融经济学普通 OCR 的发布边界、两门数学教材“省略证明 / AI 参考推导”与教材事实层混淆风险。关闭方式不是把未核定内容强行标为正确，而是把来源层、机器辅助层、派生层彻底分开，并使未核定层不再具有自动 QA / 核定数值 / 标准答案权限。

内容发布 blocker 当前为 **0**。仍保留更高等级、非阻塞的学术质量边界：金融经济学普通 OCR 未逐字符人工验收，两本数学教材未做全书独立专家证明审稿，AI/参考推导不属于教材标准答案。

## 公共财政概论

- r2 剩余 66 个表格候选已全部进入明确安全状态。
- 7 个 `VISUAL_SOURCE_TRANSCRIPTION` 保留来源视觉转录，作为 `B_SOURCE_GROUNDED` 阅读层。
- 59 个 `MACHINE_LAYOUT_AND_CELL_DRAFT` 保留 provenance，但默认发布改为 `source_image_only_table`。
- 66/66：`numeric_use_eligible=false`、`authoritative_for_automated_qa=false`。
- 原 source_record / PDF 页 / bbox / CSV / 原图引用均保留。
- r3 的阻塞型 remaining hotspots 为空；这不代表 59 个机器 CSV 已人工核定。

## 金融经济学十讲

保持 3,635 条记录：2 条 A_SOURCE_VERIFIED、42 条 B_TARGETED_SOURCE_CORRECTED、3,591 条 C_MACHINE_DRAFT。

3,591 条普通 OCR 统一降为辅助来源层：
- `reading_layer=source_ocr_auxiliary`
- `review_status=OCR_AUXILIARY_SOURCE_PAGE_AUTHORITATIVE`
- `release_completion_scope=AUXILIARY_NONBLOCKING`
- `authoritative_for_automated_qa=false`
- `qa_evidence_mode=RETRIEVAL_ONLY_REVIEW_REQUIRED`

结构扫描：重复 ID、缺页锚、页码越界、replacement char、非法控制字符、无内容记录均为 0。

## 两门数学教材

- 来源记录、公式、页锚与已有高置信修正保持不变。
- “易证 / 证明从略”等作者有意省略不再作为结构化发布 blocker。
- AI / reference derivation 保持独立派生身份。
- 没有来源标准答案时继续明确无已独立验收标准答案。
- `whole_book_mathematical_acceptance=false`。
- `reference_derivations_independently_accepted=0`。
- 发布门：`PASS_WITH_DERIVED_EXCLUDED`。

## 验证

- r3 内容检查：38 PASS / 0 FAIL
- 学习状态：29 PASS / 0 FAIL
- Go 后端：15 PASS / 0 FAIL
- Go race 子集：14 PASS / 0 FAIL
- Chromium 学习流程：42 PASS / 0 FAIL
- 发布安全 UI：4 PASS / 0 FAIL
- 最终交付检查：31 PASS / 0 FAIL

## Windows rc4

- EXE：195,388,416 bytes；SHA-256 `4297b2c20c8d5db1ada2adb313f2961d70ad7cdd03b1e5298f3271b44a413983`
- Portable ZIP：191,107,482 bytes；SHA-256 `645d39204a41411267eba8f82cafe6bec02ab0fa2ab4424119f6efb2440adfc5`
- Source-and-Tests ZIP：189,886,639 bytes；SHA-256 `d27f90f62d89f17778d6dfc628a70ff3963a4e33782e4d517d2e97cfa314b91e`

Drive 目录：`Book/03_Exports/Book-Final-r3-rc4-20260926`。三个大文件使用 64 MiB 无损分片，9 个分片全部从 Drive 重新读回；逐片 SHA-256 与重组后的三个原文件 SHA-256 均匹配。

## 仍不做的声明

1. 普通 OCR 已逐字符人工核定；
2. 所有普通正文达到出版级逐字校勘；
3. 所有数学证明均经过独立专家真值审查；
4. AI 推导等同教材标准答案；
5. 用户本人 Windows 机器已完成安装/启动/交互验收。
