# Book 当前状态 · 2026-09-23 只读选段桥候选

当前分支 `feat/reader-grant-bridge-20260923`，PR #37，Draft / Open / 未合并。最新运行代码 head `114be2a40f9e3ef364aca2e02492361ebf46e4b6`。此入口只更新本评审分支的 Book × mygpt 工作流，不替代其他分支的实时状态。原状态、原 Handoff 已按完全相同的 Git blob 保存在 `history/`，原安全规则、独立 Human Gate、不可变证据和 pending_sync 均继续有效。

## 已经完成

真实 r6 归档选段 → Book 内存授权器 → mygpt 严格接收端 → 本机 HTTP / Pydantic AI TestModel 已通过。原始转录、补录、AI 校正、思路提示、参考推导明确区分；raw/display 独立校验；取消、撤销、过期、重复请求和迟到回复受控。它不再只是合成正文演示，但仍不是手机联通或真实模型教学。

- Book：本地与远端各 68 项 Python、18 项 Node 投影测试通过。
- mygpt：两个远端干净环境各 352 项通过、0 失败、0 跳过。
- 实际 r6：95 小节，19,174 个 JS/Python 投影向量，0 差异；17,330 个有效正文、1,844 个预期空正文拒绝。不是全书数学正确性验收。
- 实际 HTTP：56 项通过，5 种实际选段路径通过 TestModel，付费模型调用 0。
- 两仓发布代码已从 CI 源归档回读一致；两个新 Drive 增量包均已完成整包及内部 manifest 校验。

## 后续 UI 状态修复

多内容层记录现在默认不选层：必须用户明确选择原文/补录/AI 校正中的一个具体层并核对预览后，分享按钮才会启用；单层记录仍可直接预选。预览阶段不会产生 `/select` 授权请求。Book CI run 35834149129：68 Python、18 投影 Node、1 项 DOM 状态回归均通过。该 DOM 测试不是实际浏览器验收。新增 v1.1 增量归档已保存到 Drive `1T_PGQxLQJgaq5BkYzlO_tAC1SXr1_arz`，旧 v1 证据保留不覆盖。

## Chromium UI + 真实后端 shim 验收

在不修改浏览器管理策略的前提下，系统 Chromium 直连 `127.0.0.1` 与 `localhost` 都仍返回 `ERR_BLOCKED_BY_ADMINISTRATOR`。为继续验证 UI，本轮使用明确的 Playwright binding 传输 shim：真实 Chromium 运行精确 Reader/Bridge JS，所有应用 fetch 由测试 harness 转发到真实 Book 127.0.0.1 服务；Book Authority、r6 源文件、mygpt BookReceiver 与实际 Pydantic AI TestModel 均不替换。

主 UI **21/21** 通过：真实 raw/display 切换、多层显式选层、预览零授权、分享、实际 TestModel 回复、MathJax、导航失效、取消迟到回复、隐藏失效、撤销、移动/桌面布局、零页面/console error。额外时序 **5/5** 通过：切模式失效、翻组失效、1 秒真实短租约先可用后过期。由于测试文档是 null origin，localStorage/history、randomUUID/WebCrypto 使用了明确测试替身，因此这仍不能冒充“浏览器直连 localhost 已通过”。

v1.2 证据归档：Drive `1l1XxGbVqS5__4RhSYevhTnNT5JT3ijs9`，1,673,673 bytes，SHA-256 `71b10b3127eb60a61681d96a9712c17758ddf7eb3f00bf09a6bdb3f75d6834ba`；整包、CRC 与 17/17 内部 manifest 已重新下载验证。旧 v1/v1.1 均保留。

## 未完成与下一步

托管浏览器以 `ERR_BLOCKED_BY_ADMINISTRATOR` 阻止 localhost 导航，未更改或绕过策略，因此 UI 端到端验收仍未完成。Android APK 身份、IPC/overlay、真机软键盘、真实教学模型、生产多用户安全和独立审阅未验收。旧 mygpt PR #5/#6 整合冲突未处理。

下一步优先做独立代码审阅；当存在允许直连 localhost 的受信任浏览器运行环境时，再用同一流程去掉传输/storage/WebCrypto 测试替身复验。Android、真实教学模型和 PR 合并仍不自动启动。

## 恢复入口

- [机器检查点](../governance/book_selection_bridge_checkpoint_20260923.json)
- [决策与验收检查点](BOOK_SELECTION_BRIDGE_CHECKPOINT_20260923.md)
- [当前增量 artifact 索引](../governance/book_selection_bridge_artifact_manifest_20260923.json)，须连同其 includes 指向的既有 artifact_manifest 读取。
- [原完整状态](history/CURRENT_STATE_before_book_bridge_20260923.md)与 [原完整交接](history/HANDOFF_before_book_bridge_20260923.md)。原文件仅作历史与继承约束依据，不能把其旧“下一步”当成本候选的新下一步。
