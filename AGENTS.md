# AGENTS.md — Book

任何 GPT / Claude / Codex / DeepSeek / 本地 Agent 接手本项目时，先读取 Google Drive 的“全项目”总入口及全部 `全项目_` 基线文件，再读取本仓库现有治理、状态与说明文件。GitHub 是项目代码、状态和治理的权威来源；Drive 是原始文件、大型/二进制产物、结果包与快照的保险库。不得只依赖聊天记忆。

## Artifact synchronization — mandatory deduplication

当用户说“更新成果”“同步所有成果”“更新 GitHub 和 Drive”“归档全部成果”或同义表达时，必须遵循 `docs/ARTIFACT_SYNC_POLICY.md`，不得解释为盲目全量重传。

硬规则：

1. 先盘点工作区、本仓库目标分支和对应 Drive 项目目录，再进行任何写入。
2. GitHub 同路径内容相同直接 `SKIP_IDENTICAL`；仅 CRLF/LF 或末尾换行差异不得制造新提交。
3. Drive 必须比较目标目录、文件名、大小和 SHA-256；完全相同则复用原 Drive ID，不重新上传。
4. 同一逻辑文件内容确实变化时，优先原位更新；只有真正的新成果才新建对象。
5. `r1/r2/r3`、run ID、时间戳、freeze、first-real、replay、calibration 等具有独立审计身份的历史成果，即使字节相同也默认保留，标记 `HISTORICAL_DUPLICATE_PRESERVED`，不得自动删除。
6. 一次逻辑同步使用最少实际需要的 GitHub commits；禁止仅为了“发布所有文件”而一文件一提交。
7. 完成后必须报告 `NEW / CHANGED / SKIP_IDENTICAL / HISTORICAL_DUPLICATE_PRESERVED / CONFLICT_NEEDS_REVIEW` 计数，以及 GitHub commit、Drive 新建/原位更新数量。
8. 同样输入连续执行两次，第二次必须产生 **0 个 GitHub 新提交、0 个 Drive 新对象**；否则同步不具备幂等性。
9. 不得因内容重复而自动删除 frozen evidence、历史运行结果或快照。
