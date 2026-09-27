# Book Windows 1.1.0 — 连续讲义版

2026-09-27，build `20260927-windows-1.1.0-continuous-r1`。本次落实用户要求：像PDF一样直接展示，而不是点一下才出来少量内容。

## 默认阅读行为

- 预习：已有导学主题的概述、先备知识、学习目标、核心知识全部展开。
- 学习：全部符合原有可展示条件的来源记录依目录连续排列，不受旧80条分页限制。长段落、证明与公式不截断。Stein默认仍是已有中文学习层，可切换索引层，不伪装成原书逐字全文。
- 复习：精编知识整理、方法和易错点全部展开，并连续展示已有来源知识记录。
- 刷题：默认题干、提示、步骤、最终答案和易错提醒连排；独立作答仍可显式进入逐题工作台，保留隐藏答案、自动保存、自评、错题和历史。

目录只跳转，不替换正文；本卷查找只定位，不隐藏其他内容。所有正文节点预先存在，MathJax在视口附近自动渲染。连读页是可重排逻辑单元，不是原PDF页码，不声称扫描版逐页复刻或新增PDF导出。

按书、模式和内容层保存稳定页标识与页内比例。已测试新开窗口恢复、译文命中定位、来源层跳转、字号12/20/72px、390/1440px宽度和深色模式。

## 实际实现和验证

此版本是artifact-backed Go/JavaScript Windows应用，不是main里的FastAPI/React。完整实现保存在固定rc4基包加本版累计源码增量中，1353个文件可恢复。GitHub的`windows/continuous-r1/continuous-core.js`只是经测试的核心代码快照，不是完整应用源码导入。

最终包内资源重新测试：JS87/87（含新增31项）、默认连续UI120/120、连续讲义356页公式渲染（89预习+89复习+178题解）、内容1150/1150（含146算例）、Go15/15、race子集14/14、可选旧工作台21/99/42项、来源显示4项、Windows PE及同源Linux服务32项，全部0失败。原知识来源过滤和质量提示未改变。

源码清单自排除1352项；连同manifest共1353项。固定rc4+本版累计增量在新目录实际恢复，逐文件与完整源码ZIP一致；重新打包/交叉编译EXE，与交付EXE逐字节一致。Portable内EXE也一致。

浏览器使用真实Chromium和最终打包资源，通过明确test-only传输桥连接隔离Linux Go服务；管理环境阻止直接loopback导航，agent-browser CLI不可用。不能称为Windows/Edge/CSP直连验收，不能称GitHub CI已通过。Windows EXE未签名，未在Windows主机执行。

## 交付与恢复

当前指针：`governance/CURRENT_WINDOWS_RELEASE.json`；全部可信身份在`governance/book_windows_1_1_0_continuous_20260927.json`。

EXE为`Book-1.1.0-Windows-x64.exe`，195606528 bytes，SHA256 `76e66f9e2794a952c9e1ce9b6b54ee5346831ed779f105d23ea05e980f64d5fd`。对话提供完整EXE、Portable及完整源码；不是旧EXE改名。

Drive目录：`Book/03_Exports/Book-Windows-1.1.0-Continuous-20260927`，ID `19bTC_WCTjWD7fdtYcDb6Y9PogSaT0XUX`。源码增量ID `11hIUGndDOqq0MPEcnIXRnvQImOpGg5lC`；报告ID `1WgDpTkGZ54u9n8dSJcoAOsoefOZghum7`。增量、报告、manifest均完成远端完整字节回读并验证SHA256。完整EXE直传Drive失败，没有虚构单EXE Drive链接。

```sh
python tools/restore_book_windows_1_0.py --baseline rc4-source.zip --delta Book-1.1.0-Source-Delta.zip --sha256 d1c6789b3e0e974f087a29604f7edf6580aadfed0c348cbdf897b9d0106ef8a1 --output NEW_DIRECTORY
```

复用既有经过测试的恢复工具与manifest契约；虽然工具名称含1_0，实际恢复版本由验证后的增量build决定。不需要先应用rc5或1.0增量，不写入已存在目录，不覆盖历史源码和个人记录。

升级前在旧版导出备份并保存退出，再运行新版。目标Windows x64且已有Edge，不需Python/Node/API Key。未分发字体。7书26195记录、845目录、89主题、269精编知识点、178配套题不变；全书精讲、全部原题已解和独立学术验收仍未完成。

保持独立Draft PR，不自动合并，不修改main或旧发布分支。后续不要重新把默认阅读改回折叠卡片；练习工作台始终是可选入口。

## 2026-09-27 全成果同步

1.1.0 的大文件 Drive 归档已经补齐：完整 EXE、Portable ZIP、完整源码 ZIP 均拆成三个不超过 64 MiB 的恢复分片。9 个分片已从 Drive 完整回读，大小与 SHA-256 逐项一致。分片清单 Drive ID：`1FP-ZRD3K91OCyPWYzHegHTmcT_t7HCWv`。

- EXE parts: `17EDymuAPM4S7fFXqElW4xsUBFzC-emeS`, `1BT7nzFqMk4ULRiidSNEq_cG0EtIhmb0X`, `1WbJVEp9r7Y3CJKfdP6z23le0PEoKCG4X`。
- Portable parts: `1KOJgjq-SNoYXAtIQ6FQzbos35NyFbrAt`, `1_Q0CA4DH5PNzAFCfKWlA0KqhfWdUlSx0`, `1r919mCT5Lrurlw9XVdVw_deiM2r1kJgW`。
- Full source parts: `1fmr1m6efwLmQ3HJYQXP99_V34VxvksNB`, `1EQAftD5XD4p-oWCt0ZtEgacGz_TSaSRL`, `1S6NTGslKTf0GWULmYhcIsxunldEpvD4_`。

Drive 单文件 EXE 仍不声明存在；对话附件继续提供完整单文件下载。历史 rc4/rc5/1.0 归档不覆盖、不删除。
