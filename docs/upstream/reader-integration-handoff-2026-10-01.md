# 原创单章阅读器：整合候选交接

检查点：2026-10-01 01:56 UTC。目标仓库 `Jvust1/Book`。

## 先分清 main、已验证代码和本候选

- 实时 main：`805510f86546709b6f67c9e9079943f205c2c245`，PR #57 的合并提交。本轮没有合并、部署或修改仓库可见性。
- 已验证父代码：[PR #75](https://github.com/Jvust1/Book/pull/75)，`5616246fbf88c8a3a0a8732d0e36c5a11c6c6f3b`。
- 整合分支：`docs/coherent-reader-candidate-20261001`，面向 main 的 Draft。该分支仅在 #75 上补充本交接、状态说明、包内交接清单与对应归档测试；没有新增运行时依赖或改变既有工作流。新提交自身的验收必须看其 exact-head runs，不能沿用父提交的绿色状态。
- 保留历史 PR：#58–#70、#72–#75。#66 首次连接阅读器与独立 SymPy 加固；#69 是第一次 main-targeted 源码交付；之后的回执、身份、错误响应及 Windows 验收都在本候选中。
- **#71 未纳入。** 该目录响应/导航恢复分支的六条新浏览器恢复用例失败；原有五条原创旅程通过不能抵消该失败。没有把它的生产代码、测试或诊断改动复制到本候选。#71 的诊断日志发布仍暂停，必须另获明确批准；该边界也适用于替代诊断方案，不能借本整合候选发布。
- 独立教材审校、旧 Windows/Android 应用和 #35 时区修复等分支保持各自历史，不在此处合并。

## 用户能走通的实际路径

原创章节由 `app_tests.synthetic_pilot_server:create_app` 创建隔离临时文件和 SQLite，使用真实 BookAppService、Runtime、API DTO 与前端。问答生成端仅换成确定性测试提供者，不需付费模型或 API key。

1. 进入原创课程、章节与小节，使用预习、学习、复习、刷题四个入口。KaTeX 排版显式数学字段/定界公式，并保留原文。
2. 点击已验证来源，SourceResolver 返回结构化来源；选择自己的合法本地 PDF 后，PDF.js 按物理页呈现，Fuse.js 对限定页段做本地提取与模糊检索，命中返回物理页。
3. 教材问答走真实检索、EvidenceGate 与引用校验；react-markdown 组织答案，只有现有验证后引用卡能执行来源导航。格式化不提升模型答案权威性。
4. Source/Search 通过 TanStack Query 去重、取消与临时复用；Zod 验证响应结构和请求身份。服务器拒绝、格式错误或错课程响应不会被旧缓存遮住。
5. 刷题页的 math.js Worker 提供显式计算/取消/清除。独立 SymPy CLI 在同一测试旅程中通过真实子进程检查原创代数等价式，返回三态结果；没有新增浏览器评分接口或自动判分。
6. 学习状态仍由服务器 SQLite 保存：触达为 0，显式完成为 100，完成后不倒退。错误回执显示“保存尚未确认”，不自动重发；真实已提交记录经正常重载恢复。阻断/耗尽 sessionStorage 时只保留有限临时视图状态，提示重载丢失风险。

## 当前官方上游核验

以下星数来自 2026-10-01 01:55 UTC 的官方 GitHub REST 仓库响应；星数是时间点记录。精确 npm integrity、上游提交、源码调用与未改写许可证见各专项文档及 lockfile。本次没有为了数量升级版本。

| 项目 | 精确版本 | 官方 stars | 许可证 | 真实调用 / 专项记录 |
| --- | --- | ---: | --- | --- |
| [KaTeX](https://github.com/KaTeX/KaTeX) | 0.18.10 | 20,414 | MIT | `render` / upstream auto-render；[记录](katex-reader-2026-09-30.md) |
| [PDF.js](https://github.com/mozilla/pdf.js) | pdfjs-dist 6.3.289 | 53,966 | Apache-2.0 | `getDocument/getPage/render/streamTextContent`；[记录](pdfjs-local-source-2026-09-30.md) |
| [react-markdown](https://github.com/remarkjs/react-markdown) | 10.1.0 | 15,899 | MIT | QAAnswerContent 的真实解析器；[记录](react-markdown-qa-2026-09-30.md) |
| [math.js](https://github.com/josdejong/mathjs) | 15.2.0 | 15,079 | Apache-2.0 | Worker 内 `parse/compile/evaluate/format`；[记录](mathjs-practice-2026-09-30.md) |
| [Fuse.js](https://github.com/krisk/Fuse) | 7.5.0 | 20,496 | Apache-2.0 | 本地 PDF 页段的 `Fuse.search`；[记录](fuse-local-pdf-search-2026-09-30.md) |
| [Zod](https://github.com/colinhacks/zod) | 4.6.5 | 44,047 | MIT | API/缓存的 strict schema/refinement；[记录](zod-source-contracts-2026-09-30.md) |
| [TanStack Query](https://github.com/TanStack/query) | react-query/query-core 5.104.0 | 50,386 | MIT | QueryClient/QueryCache/useQuery/AbortSignal；[记录](tanstack-reader-cache-2026-09-30.md) |

以上为七个新接入项目。既有 [SymPy](https://github.com/sympy/sympy) 1.14.0（14,981 stars）仅计安全加固：核心 BSD-3-Clause，完整 LICENSE 同时含第三方组件说明，GitHub aggregate 为 NOASSERTION，不能简化为整包单一许可。既有 [Playwright](https://github.com/microsoft/playwright) 1.62.1（96,927 stars，Apache-2.0）用于真实浏览器和 Windows 进程生命周期验收，不计为新接入项目。

许可证保留在 `app/web/public/licenses/`、PDF.js 原始资源目录和 `docs/upstream/licenses/SymPy-1.14.0-LICENSE.txt`；math.js NOTICE 也保留。辅助 remark 插件不计入七项目。Book 自有代码没有因此获得额外再许可声明。

## 已执行的验收证据（仅限父代码 5616246）

| exact-head gate | 结果 | 直接证据 |
| --- | --- | --- |
| Windows 干净源码 | 19 个归档测试、40 个提取后 Python、403 个 Web、typecheck/build、5 条原创 Chromium 旅程全部通过；浏览器 0 retries | [run 36801911156](https://github.com/Jvust1/Book/actions/runs/36801911156) |
| Linux 干净源码 | 同一源清单与锁，19 归档、40 Python、403 Web、typecheck/build、5 原创旅程全部通过；0 retries | [run 36801911159](https://github.com/Jvust1/Book/actions/runs/36801911159) |
| 完整 Book UI | 3 jobs 通过；38 常规 + 5 原创 = 43 条不同浏览器用例，0 retries | [run 36801911199](https://github.com/Jvust1/Book/actions/runs/36801911199) |
| Runtime | Python 3.11 / 3.12 / 3.13 三个 job 通过 | [run 36801911161](https://github.com/Jvust1/Book/actions/runs/36801911161) |

Windows 最初的 run 36801301872 有一个归档测试失败：测试 spy 未把允许打开的 manifest 路径按生产逻辑 resolve；其余 18 个归档测试通过。最后仅修正 spy 的路径比较，不修改生产逻辑或放宽断言，随后上表 final head 全部通过。失败历史保留。

五条原创旅程为桌面端与窄屏完整路径、sessionStorage 不可访问、写入超额、真实 SQLite commit 后畸形回执与重载恢复。跨系统重跑这五条并不增加独立用例数。窄屏/桌面原创建图检查不代表所有设备与全书字体验收。

从两个成功 run 下载、解压并验证的 #75 内层源码包均为 287,981 bytes / 183 source files，SHA-256：

`272003b51c9f8ae57b954c4a72daafdc796006762f684ee137e28476bc5272a9`

这两个实际环境产物逐字节相同；不声称所有 Python/zlib 版本或应用二进制都逐字节相同。清单记录 source_commit、每文件 source_path/mode/size/SHA-256。它不是签名发布者证明。本交接加入后会形成新的 source_commit/清单/哈希，不能复用此旧哈希认证新包。旧 #69 与 #75 交付保留各自版本。

## 复现与包边界

运行步骤以 [包 README](reader-pilot-package-README.md) 为准：Python 3.13、Node 22、隔离 venv、hash-pinned pip、`npm ci --no-audit`。Windows 使用 PowerShell 的直接 venv Python 与进程级 PATH，不改 execution policy。`playwright.portable.config.ts` 自行启动和关闭原创 API / Vite preview，拒绝复用已有端口。

源码包只包含允许列出的代码、锁、许可证、原创合成测试与这些文档；不包含 canonical `books/`、`courses/`、`library/`，用户 PDF、密钥、数据库、依赖目录或原生安装器。提取前完整验证路径和清单，拒绝 Windows ADS/设备名/大小写碰撞等不可移植输入，不静默改名。本交接作为可选 v1 条目加入；旧 v1 包继续可验证、可重建。

安装依赖需要网络，阅读测试不请求付费模型。可选 npm audit 在后续批次未运行；不得继承旧文档某一时间点的“0 漏洞”作为当前安全结论。

## 教材与产品仍待独立验收的事项

外部[六书报告](https://github.com/Jvust1/Book/blob/6d7ecf5969ed1feffc1061dc6bdb68aff77fd708/audits/2026-10-01/six-books_0800_acceptance.md)位于 `audit/six-books-20261001-0800` 分支，状态 PARTIAL / FAIL。这里只核对报告与分支身份，没有重新扫描其 PDF：

- 报告涉及 24 PDF / 3477 页；五书合计 2733 页非 A4，需要从结构化源重排，不能用破坏式裁切或缩放代替。
- 当代中国经济隐藏文本层报告 578 个 NUL，抽样未看到对应可见破损；需来源重建再验。
- 同日报告中逐书专业审校及二进制同步证据不完整。不能把“没有新确认知识错误”解释成“全部内容无错误”。

本代码候选没有导入、修改或重新发布这些教材资产。以下能力仍不能从此包推出：

- 选中文件的教材/版本真实性、canonical PDF 自动绑定、精确页内几何锚点、OCR 或完整交互注释。
- 整本教材的知识、题解、排版、A4 或全部字体质量；用户 Windows/Android 设备、原生 exe/APK 和离线依赖安装器。
- 真实付费模型质量或自动评分。math.js 是有限精度计算；SymPy 对缺少域假设等不确定输入保持 unknown，Windows 没有与 POSIX 相同的硬内存限制。
- 所有响应的持续时间上限。已有成功 JSON 2 MiB 与错误 JSON 64 KiB ceiling 限制消费字节；不保证服务器停顿时长、底层单个 chunk 分配或操作系统安全沙箱。
- #71 Library/Course/Chapter 目录契约与恢复问题已经解决。

下一步先评审 main-targeted Draft 的精确差异并完成其全套 gates；教材、目录恢复、原生交付和合并决策分开保留证据与授权，不用“所有完成”概括。
