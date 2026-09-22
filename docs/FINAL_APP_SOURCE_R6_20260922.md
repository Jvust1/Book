# Book 双课程 r6 最终 App 源码候选

日期：2026-09-22。

这是将 **r6 第一基础源码 + Batch5 累计增量** 合并后的单包完整源码树。它不需要再依次叠加 Batch2/3/4/5。

## 当前 UI 修订（2026-09-22）

- “学习”正文改为高密度连续阅读流：多条来源记录在同一阅读卡内顺序排版，减少卡片割裂。
- 学习模式单页容量提高到 80 条记录；跳转逻辑与真实 Chromium 测试已同步，不再依赖旧的 24 条分页假设。
- 正常学习正文不再显示 `来源 chXX-... / 纸书页 / PDF 页` 等行内来源标签；**来源/provenance 数据仍完整保留在结构化数据、原页入口、修正证据和内部字段中**，只是默认阅读界面隐藏。
- 预习、复习、刷题仍保留需要的来源/证据入口，不把内部可追溯性从数据层删除。

当前 Android 可安装包另行归档为 `Book-App-CURRENT-r6-batch5.apk`。该 APK 是在已验证的 0.1.4 Android/Chaquopy 壳上离线替换当前 r6 Python/reader/coursepacks 资源并重新签名得到，**不是一次新的 Gradle clean build**。APK ZIP 与 v2 签名内容摘要已验证，当前 SHA-256 为 `012527c4d3e1d24ce3560394f44ededfd046e25f0d63356aaa844926543a8208`。

## 已包含

- Android 工程：`android-app/`，Chaquopy + 内置 FastAPI/Python Runtime + WebView 前端；构建时直接打包当前 `coursepacks/**`。
- Web/桌面/Runtime/测试源码及双课程完整当前结构化数据。
- 预习、学习、复习、刷题四板块。
- PDE 3,790 条来源记录、6,903 段来源公式；FA 5,565 条来源记录、9,342 段来源公式。
- FA 110 道题的 AI 参考推导草稿（30 份历史 + Batch5 新增 80 份），均非官方答案。
- 13 项分层修正（source 原文不覆盖；correction 与 derived 分离）。
- Batch5 全量结构审计、公式检查、浏览器验证及恢复证据。
- 48 条“易证/从略/留给读者”语言线索已全部做结构语义分类：它们不是因此被证明正确，只是不再作为“未分类结构错误”排队。

## 仍然没有冒称完成的事项

- 两本教材没有经过独立数学专家逐条验收；`full_verified_content` 仍为 `INCOMPLETE`。
- 2 项明确数学问题仍 OPEN，2 项 MEDIUM correction 仍只作校注。
- PDE 完整 worked solutions 仍不齐全。
- Android/ARM64 实机、原生书宋和字号设置跨重启持久化仍未做最终设备验收。
- 当前 APK 是离线资源重打包交付，不等同于从当前源码完成一次联网 Gradle clean rebuild。

## Android 正常源码构建

需要 Android SDK 35、JDK 17、Python 3.11、Node.js 22/npm。

```bash
cd app/web
npm ci
cd ../../android-app
./gradlew assembleDebug
```

Windows 使用 `gradlew.bat`。输出通常位于 `android-app/app/build/outputs/apk/debug/app-debug.apk`。

## 当前验证口径

最新 UI 修订后重新执行：

- `tests/`：349 passed + 184 subtests。
- `app_tests/`：111 passed + 55 subtests。
- `tests_reader/`：130 passed。
- 合计：590 tests + 239 subtests PASS。
- 真实 Chromium 定向检查：20/20 PASS；覆盖 reader.js、离线 MathJax、FastAPI/SQLite bridge、四模式、修正层、字体范围和页面错误检查。
- APK：ZIP CRC/Python 资源检查 PASS；APK Signature Scheme v2 RSA 与内容摘要 PASS。

Batch5 原有 17,248/17,248 MathJax 语法/渲染证据和内容完整性证据继续保留；本次 UI 修订没有改教材 source/correction/derived 数据。

## 数据原则

- `source`：教材来源，保留。
- `correction`：模型/验证得到的修正版，带理由、证据、置信度。
- `derived`：学习提示、解题推导等 AI 内容，不冒充教材或官方答案。

本文件是当前完整源码候选入口；GitHub `main` 未因该候选自动修改，PR #33 仍保持 Draft / 未合并。
