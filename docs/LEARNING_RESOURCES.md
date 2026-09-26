# Book：5 本书与开源参考项目

书目查证：2026-09-22 至 2026-09-26；GitHub 元数据复核：2026-09-26（UTC，北京时间 9 月 27 日）。

已核对最新内容审校分支 PR #38：七书规范内容及 Windows rc4 已形成交付候选，当前内容质量层发布 blocker 为 0。来源映射、公式显示与学习任务仍是持续质量工作；更高等级数学/学术验收和用户 Windows 真机验收需分别完成。旧路线图的“当代中国经济正文为零”等描述属于早期起点，不作为本次资源选择的当前事实。

成长次序见[长期路线图](LONG_TERM_ROADMAP.md)。本清单包含 **5 本书、13 项 GitHub 参考**；按项目能力与使用范围扩大来选择，不按月份排课。

本次现状依据：[开发 PR #38](https://github.com/Jvust/Book/pull/38)、[读取时的固定版本](https://github.com/Jvust/Book/tree/84208b842e79842e3963fb68e602d696039c9cd3)。这些是开发分支证据，不代表已经合并或完成用户设备验收。

## 先从哪里开始

先读两本的相关章节：[PDF Explained](https://www.oreilly.com/library/view/pdf-explained/9781449321581/)；[Make It Stick: The Science of Successful Learning](https://www.makeitstick.com/about-make-it-stick)。

先看三个仓库：[jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)、[pydantic/pydantic](https://github.com/pydantic/pydantic)、[mathjax/MathJax](https://github.com/mathjax/MathJax)。

第一项可评审产物：制作 10 页代表性样本的物理页/印刷页/文本框/原图映射表，并列出乱码、跨页和图表错误类型。

| 成长环节 | 用户价值 |
|---|---|
| G1 单门可信教材 | 能看完整原文并定位来源与疑点 |
| G2 完整课程学习 | 能围绕同一课程持续预习、学习、复习、刷题 |
| G3 可重复的多课程生产 | 新教材可沿同一流程进入 App |
| G4 个人学习系统 | 多门课程、记录和复习相互关联且可恢复 |
| G5 有条件的学习协作 | 允许其它工具提供帮助而不夺走内容权威 |

P0＝当前先学；P1＝能力深化时参考；P2＝需求成立后再评估。推荐指向学习或候选比较，没有承诺安装全部依赖。

## 五本书：用途与最小产物

### 1. PDF Explained

- 作者：John Whitington。
- 版本：一手页面未明确版次；语言：英文；本次未核验中译本。
- [出版社／作者入口](https://www.oreilly.com/library/view/pdf-explained/9781449321581/)。O’Reilly 官方购阅/订阅；页面列为 2011 年出版，未注明版次
- 对应成长：G1、G3。
- 解决的问题：理解页对象、文字坐标、字体映射、图像与书签，解释为何提取成功仍可能漏正文或图表；这是来源审校方法，不是绕过 PDF 权限的方法。
- 最小应用产物：制作 10 页代表性样本的物理页/印刷页/文本框/原图映射表，并列出乱码、跨页和图表错误类型。

### 2. Make It Stick: The Science of Successful Learning

- 作者：Peter C. Brown / Henry L. Roediger III / Mark A. McDaniel。
- 版本：一手页面未明确版次；语言：英文原著；作者官网确认简体及繁体中文版本入口，译本版次未核验。
- [出版社／作者入口](https://www.makeitstick.com/about-make-it-stick)。作者官网提供正规购书、出版社和中文版本入口；仅节选公开，非全书免费
- 对应成长：G2、G4。
- 解决的问题：把复习和刷题设计为可回忆、可反馈的任务，防止将重复阅读、在线时长和点击次数直接当作掌握。
- 最小应用产物：为同一教材小节设计 1 组自由进入的预习/学习/复习/练习任务，加入延迟回忆题与答案来源，不承诺学习提升百分比。

### 3. Don’t Make Me Think, Revisited: A Common Sense Approach to Web (and Mobile) Usability

- 作者：Steve Krug。
- 版本：第 3 版，2014；语言：英文原著；作者官网确认有中文版本，中文书名/译本版次未核验。
- [出版社／作者入口](https://sensible.com/dont-make-me-think/)。作者官网正规纸书/电子书入口及样章；不是免费全书
- 对应成长：G2。
- 解决的问题：解决章节定位、四种入口、来源回链和大字号阅读中的理解负担，先修阅读阻断再加功能。
- 最小应用产物：完成 5 个真实任务的观察表：找章节、看原图、切模式、调字号、恢复位置；记录失败步骤并做一轮修正。

### 4. Python for Data Analysis

- 作者：Wes McKinney。
- 版本：第 3 版，2022；作者开放版持续修勘；语言：英文；本次未核验中译本。
- [出版社／作者入口](https://wesmckinney.com/book/)。作者官网合法免费 HTML 全书；正文保留版权，开放阅读不等于可复制进课程包；另有纸书/电子书购买入口
- 对应成长：G1、G3。
- 解决的问题：用表格化检查汇总页覆盖、题目身份、重复块和 QC 分类，帮助多课程导入保持可审计；不以自动清洗改写原文。
- 最小应用产物：从现有 manifest 生成只读 QC 表：来源、页区间、类型、风险、状态、下一动作；不覆盖原始识别结果。

### 5. Designing Data-Intensive Applications

- 作者：Martin Kleppmann / Chris Riccomini。
- 版本：第 2 版，2026（采用所列官方页面对应版本）；语言：英文；本次未核验第 2 版中译本，不以第 1 版译本冒充。
- [出版社／作者入口](https://martin.kleppmann.com/2026/03/24/designing-data-intensive-applications-2e.html)。作者出版记录核验版本与作者，并提供正规购书入口；不是免费全书
- 对应成长：G3、G4、G5。
- 解决的问题：理解数据身份、事务、幂等、复制和版本演进的取舍，用于课程包和学习记录恢复；不是增设分布式平台的理由。
- 最小应用产物：写一份课程包/StudyRecord 的版本、重复导入、UTC、冲突与恢复决策记录；保留 SQLite，迁移需单独验证恢复与兼容性。

## GitHub 参考总览

许可摘要是本轮筛选依据；最近推送不等于稳定发行、可靠性或本项目兼容性。仓库代码的许可与模型权重、数据、字体、图片及角色素材的许可分别核对。

| 优先级 | 官方仓库 | 成长环节 | 许可摘要 | 已归档 | 最近推送（UTC） |
|---|---|---|---|---|---|
| P0 | [jsvine/pdfplumber](https://github.com/jsvine/pdfplumber) | G1、G3 | MIT | 否 | 2026-08-06T00:46:50Z |
| P0 | [pydantic/pydantic](https://github.com/pydantic/pydantic) | G1、G3 | MIT | 否 | 2026-09-26T17:31:26Z |
| P0 | [mathjax/MathJax](https://github.com/mathjax/MathJax) | G1、G2 | Apache-2.0 | 否 | 2026-07-03T13:37:32Z |
| P1 | [py-pdf/pypdf](https://github.com/py-pdf/pypdf) | G1、G3 | BSD-3-Clause（LICENSE 人工核对；API=NOASSERTION） | 否 | 2026-09-26T15:07:02Z |
| P1 | [ocrmypdf/OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | G1、G3 | MPL-2.0 | 否 | 2026-09-22T07:31:10Z |
| P1 | [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) | G1、G3 | Apache-2.0 | 否 | 2026-09-11T05:17:27Z |
| P1 | [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | G1、G3 | Apache-2.0 | 否 | 2026-09-16T03:31:50Z |
| P1 | [mozilla/pdf.js](https://github.com/mozilla/pdf.js) | G1、G2 | Apache-2.0 | 否 | 2026-09-25T06:04:33Z |
| P1 | [remarkjs/remark](https://github.com/remarkjs/remark) | G3 | MIT | 否 | 2026-09-24T10:45:01Z |
| P1 | [microsoft/playwright](https://github.com/microsoft/playwright) | G2、G3 | Apache-2.0 | 否 | 2026-09-26T05:40:18Z |
| P2 | [zotero/zotero](https://github.com/zotero/zotero) | G3、G4 | AGPL-3.0 主体；第三方部分另记 | 否 | 2026-09-25T19:03:52Z |
| P2 | [ankitects/anki](https://github.com/ankitects/anki) | G2、G4 | AGPL-3.0-or-later 主体；含 BSD-3-Clause/MIT/Apache-2.0/CC 等部分 | 否 | 2026-09-25T20:51:07Z |
| P2 | [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki) | G4 | MIT | 否 | 2026-08-14T03:34:18Z |

## 各仓库具体怎么用

### 1. jsvine/pdfplumber · P0

- 使用方式：候选接入：离线提取工具；适用阶段：G1、G3。
- 本项目用途：数字原生 PDF 的字形、坐标和表格提取适合建立来源回链；最小产物是 10 页文字框/表格与原页对照报告。
- 适用限制：官方说明更适合机器生成 PDF；扫描页不能因无文本就判空白，提取结果必须回看原页。
- 查证：[官方仓库](https://github.com/jsvine/pdfplumber) · [许可依据](https://github.com/jsvine/pdfplumber/blob/stable/LICENSE.txt) · [维护元数据](https://api.github.com/repos/jsvine/pdfplumber)。

### 2. pydantic/pydantic · P0

- 使用方式：候选接入：数据合同校验；适用阶段：G1、G3。
- 本项目用途：为原文、校注、推导、来源锚点与 QC 定义独立模型；最小产物是合法/缺来源/串版本 3 类课程包的校验报告。
- 适用限制：结构合法不等于数学正确；V1/V2 有差异，不顺便升级现有运行时或引入云观测服务。
- 查证：[官方仓库](https://github.com/pydantic/pydantic) · [许可依据](https://github.com/pydantic/pydantic/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/pydantic/pydantic)。

### 3. mathjax/MathJax · P0

- 使用方式：承接现有使用；按版本学习；适用阶段：G1、G2。
- 本项目用途：已有公式显示链的直接参考；最小产物是 20 个长公式/换行/大字号/辅助阅读的展示检查。
- 适用限制：此库是打包版本，源码开发另在 MathJax-src；渲染成功不替代原式核对或数学独立审查。
- 查证：[官方仓库](https://github.com/mathjax/MathJax) · [许可依据](https://github.com/mathjax/MathJax/blob/master/LICENSE) · [维护元数据](https://api.github.com/repos/mathjax/MathJax)。

### 4. py-pdf/pypdf · P1

- 使用方式：候选接入：离线页级工具；适用阶段：G1、G3。
- 本项目用途：读取页数、元数据、书签和拆分审校样本；最小产物是物理页范围与原件 SHA 对应的页清单。
- 适用限制：LICENSE 人工核对为 BSD 3 条款式，API 返回 NOASSERTION；不是 OCR，不覆盖原件，也不绕过访问限制。
- 查证：[官方仓库](https://github.com/py-pdf/pypdf) · [许可依据](https://github.com/py-pdf/pypdf/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/py-pdf/pypdf)。

### 5. ocrmypdf/OCRmyPDF · P1

- 使用方式：条件接入：隔离的扫描预处理；适用阶段：G1、G3。
- 本项目用途：给授权扫描 PDF 添加可搜索文字层，便于审校；最小产物是原件不变、派生件单独哈希的 OCR 比较包。
- 适用限制：主项目 MPL-2.0；第三方可执行文件/依赖各有许可。文字层不是正文验收，原图/公式仍需回看；先评估运行资源。
- 查证：[官方仓库](https://github.com/ocrmypdf/OCRmyPDF) · [许可依据](https://github.com/ocrmypdf/OCRmyPDF/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/ocrmypdf/OCRmyPDF)。

### 6. tesseract-ocr/tesseract · P1

- 使用方式：候选接入：本地 OCR 基线；适用阶段：G1、G3。
- 本项目用途：作为成本可控的传统 OCR 比较基线，区分识别、版面和人工校注；最小产物是普通正文与低质量页的错误分类。
- 适用限制：模型语言数据和版本单独登记；不自动解决表格、复杂公式与跨页阅读顺序，不预承诺识别率。
- 查证：[官方仓库](https://github.com/tesseract-ocr/tesseract) · [许可依据](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/tesseract-ocr/tesseract)。

### 7. PaddlePaddle/PaddleOCR · P1

- 使用方式：条件接入：中文/版面/公式候选；适用阶段：G1、G3。
- 本项目用途：中文、公式、表格的结构化能力与经济教材 QC 相符；先比较现有工具，产出同一代表样本的错误、时间、显存报告。
- 适用限制：官方宣传或榜单分数不外推到本书；模型权重、依赖许可与下载成本另核。按真实 RAM/显存规划，大缓存放 D 盘。
- 查证：[官方仓库](https://github.com/PaddlePaddle/PaddleOCR) · [许可依据](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/PaddlePaddle/PaddleOCR)。

### 8. mozilla/pdf.js · P1

- 使用方式：条件接入：来源对照查看；适用阶段：G1、G2。
- 本项目用途：在浏览器侧定位原 PDF 页和疑点区域；最小产物是 10 个正文/图表/公式锚点可回到正确物理页的原型。
- 适用限制：PDF 查看和教材正文结构是不同层；不把在线 viewer 变成获取缺失原件的手段，字体和授权随原件核验。
- 查证：[官方仓库](https://github.com/mozilla/pdf.js) · [许可依据](https://github.com/mozilla/pdf.js/blob/master/LICENSE) · [维护元数据](https://api.github.com/repos/mozilla/pdf.js)。

### 9. remarkjs/remark · P1

- 使用方式：候选接入：Markdown AST 工具；适用阶段：G3。
- 本项目用途：利用语法树检查标题、题目、引用与公式节点，减少正则改写造成的内容损失；最小产物是两份教材样本无语义丢失的转换差异报告。
- 适用限制：插件可改写内容，默认只检查；转换前后保留身份和哈希，不能统一排版时顺手删除证明或合并异名概念。
- 查证：[官方仓库](https://github.com/remarkjs/remark) · [许可依据](https://github.com/remarkjs/remark/blob/main/license) · [维护元数据](https://api.github.com/repos/remarkjs/remark)。

### 10. microsoft/playwright · P1

- 使用方式：候选接入：前端回归；适用阶段：G2、G3。
- 本项目用途：自动检查四入口、窄屏大字号、来源跳转和离线提示；最小产物是能发现裁切和错误章节回链的少量任务测试。
- 适用限制：浏览器测试不替代 Android 真机、Windows 构建和实际记录恢复；只测试本项目授权环境。
- 查证：[官方仓库](https://github.com/microsoft/playwright) · [许可依据](https://github.com/microsoft/playwright/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/microsoft/playwright)。

### 11. zotero/zotero · P2

- 使用方式：只读学习：来源与版本组织；适用阶段：G3、G4。
- 本项目用途：学习书目、附件、批注与引用身份分离；最小产物是 Book 最小书目字段及同书异版匹配规则。
- 适用限制：主许可 AGPLv3，第三方部分另记；不整库嵌入，不将收藏到附件等同教材再分发授权，不另造内容权威。
- 查证：[官方仓库](https://github.com/zotero/zotero) · [许可依据](https://github.com/zotero/zotero/blob/main/COPYING) · [维护元数据](https://api.github.com/repos/zotero/zotero)。

### 12. ankitects/anki · P2

- 使用方式：只读学习；必要时标准导出原型；适用阶段：G2、G4。
- 本项目用途：观察练习卡、复习记录与撤销的交互，最小产物是 10 张来源可追溯卡的字段映射方案。
- 适用限制：AGPL-3.0-or-later 主体，多许可证组成；不复制实现进本库，不把卡片复习替代完整原文学习。
- 查证：[官方仓库](https://github.com/ankitects/anki) · [许可依据](https://github.com/ankitects/anki/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/ankitects/anki)。

### 13. open-spaced-repetition/fsrs4anki · P2

- 使用方式：只读学习：有数据后比较调度；适用阶段：G4。
- 本项目用途：研究间隔复习如何使用真实复习记录；最小产物是现有手动复习与候选算法的离线比较方案。
- 适用限制：这是 Anki 适配项目，不直接当 Book SDK；没有可靠记录、足够样本或可关闭机制时不接入，不承诺记忆收益。
- 查证：[官方仓库](https://github.com/open-spaced-repetition/fsrs4anki) · [许可依据](https://github.com/open-spaced-repetition/fsrs4anki/blob/main/LICENSE) · [维护元数据](https://api.github.com/repos/open-spaced-repetition/fsrs4anki)。

## 检索覆盖与未采用项

本清单按以下环节筛选，不能穷尽 GitHub。成长适配、优先级和应用产物是结合本项目的建议；书目身份、许可和维护状态依据链接中的一手来源。

- PDF 页结构、文本/表格提取、扫描 OCR、中文/公式候选
- 原文/校注/推导分层、版本合同和来源管理
- 离线公式/原件显示、阅读可用性与前端回归
- 多课程可重复导入、学习记录与条件复习调度
- 出版社/作者书目、官方 README、GitHub API 元数据；不是穷尽全部 GitHub

以下未采用项的细节沿用初次筛选证据；不把未入选项目说成永久不可用。

- **非授权整书镜像/教材 PDF 合集**：没有教材使用和再分发授权不能作为导入来源；开放阅读也不自动允许正文复制。 [依据](https://wesmckinney.com/book/)

## 使用这份清单的方式

每次从当前成长环节选一本书的一部分和一至三个相关仓库，先形成小产物，再决定是否接入。实际采用时固定版本，核对当前官方文档、许可证和项目已有实现。旧书中的 API 示例以现行官方文档为准。

本次交付是书目和公开项目研究：未购买或复制整书，未安装或运行候选项目，也没有把候选能力计作本项目的已验证成果。
