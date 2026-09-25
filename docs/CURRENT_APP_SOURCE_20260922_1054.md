# CURRENT App 源码入口 — 2026-09-22 10:54 +08:00

用户指出先前提供的 `Book-App-Final-Source-r6-batch5.zip` 是旧逻辑包，不能把今天的 Drive 登记时间等同于源码刚刚生成。

因此本次从最新合并的 r6 Batch5 源码树**重新打包**：
- `Book-App-Source-CURRENT-r6-20260922.zip`
- Drive ID: `1UiVow02Huh3r8qKBH8v4bL3D9OfkQ8_R`
- bytes: 70,348,611
- SHA-256: `c376dd1314838a49682d56f94c6c22a20868358609f4d7c4058a80ce37be5dee`

这不是给旧 ZIP 改名：新包加入 `CURRENT_HANDOFF.json`、`CURRENT_README_zh.md`、fresh validation logs 和重新生成的 `CURRENT_SOURCE_MANIFEST.json`。内部 1,554/1,554 文件哈希重新计算并通过；Drive 完整回读后 SHA-256 与本地完全一致，ZIP CRC PASS。

源码业务逻辑/课程数据仍是 r6 Batch5，因为 Batch5 之后没有新的 app 业务代码或课程内容变更；后续 GitHub 写入只是归档/治理入口。当前重新执行验证：590 tests +239 subtests PASS，integrity PASS，FA source-entry identity PASS，20项 Chromium 检查 PASS。Android Gradle 在当前云环境中因为无法解析 `services.gradle.org` 而在下载 wrapper 阶段停止，尚未进入编译；不冒称 APK 已重新构建。

旧 `Book-App-Final-Source-r6-batch5.zip` 保留为历史证据，不删除、不覆盖。PR #33 继续 Draft，main 不修改。
