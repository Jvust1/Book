# Book 双课程 r6 最终 App 源码候选

日期：2026-09-22。

这是将 **r6 第一基础源码 + Batch5 累计增量** 合并后的单包完整源码树。它不需要再依次叠加 Batch2/3/4/5。

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
- Android/ARM64 实机、原生书宋和字号设置跨重启持久化仍未做最终设备验收；本包是源码，不是 APK。

## Android 构建

需要 Android SDK 35、JDK 17、Python 3.11、Node.js 22/npm。

```bash
cd app/web
npm ci
cd ../../android-app
./gradlew assembleDebug
```

Windows 使用 `gradlew.bat`。输出通常位于 `android-app/app/build/outputs/apk/debug/app-debug.apk`。

## 当前验证口径

Batch5 冻结结果：590 Python tests + 239 subtests；17,248/17,248 MathJax 语法/渲染；20 项真实 Chromium 定向检查；基础包+Batch5 增量恢复 1,535 文件一致。最终源码打包后又重新验证：1539/1539内部文件哈希通过，590 tests + 239 subtests通过，完整性与FA来源身份检查PASS。当前云环境无法解析services.gradle.org，故本轮没有重新执行Gradle Android编译；这不是编译失败。

## 数据原则

- `source`：教材来源，保留。
- `correction`：模型/验证得到的修正版，带理由、证据、置信度。
- `derived`：学习提示、解题推导等 AI 内容，不冒充教材或官方答案。

本文件是最终源码候选入口；GitHub `main` 未因该候选自动修改，PR #33 仍不自动合并。
