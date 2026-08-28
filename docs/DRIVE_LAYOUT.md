# Book Google Drive 目录与同步约定

更新时间：2026-08-28

Google Drive 项目根目录：`Book`

## 1. 当前真实目录

```text
Book/
├── 00_Project/
│   ├── GitHub_Sync/
│   └── External_References/
│       ├── Notes/
│       └── Snapshots/
├── 01_Textbooks/
├── 02_Lectures/
├── 03_Exports/
└── 04_Backups/
```

以上是当前实际存在的项目目录。`External_References` 因本项目已进入真实源码级对标而创建，用于固定版本第三方参考资料；其中完整源码快照尚未归档完成，状态由 `governance/pending_sync.json` 跟踪。未来同步和 Meeting 等其他目录只在对应功能阶段创建，不提前制造无用途空目录。

## 2. GitHub 与 Drive 的职责

### GitHub

GitHub 是代码、项目状态与治理权威，主要保存：

- 源代码
- Schema / API contract
- Runtime 与 processing rules
- 产品规范
- Current State / Roadmap
- 测试 / CI
- 适合版本管理的小型结构化治理数据

### Google Drive

Drive 是原始文件、大型产物和未来用户同步数据的保险库，主要保存：

- 原始教材 PDF
- 原始课堂录音
- 私有 Meeting 录音
- 用户附件
- 同步包 / processing bundles
- 大型生成结果
- exports / snapshots / backups

原始录音和大型 PDF 不提交 GitHub。

## 3. `00_Project`

保存非代码项目资料和 GitHub/Drive checkpoint 状态。

当前：

```text
00_Project/
├── GitHub_Sync/
└── External_References/
    ├── Notes/
    └── Snapshots/
```

`GitHub_Sync` 可保存：

- CURRENT 同步状态
- 阶段性 artifact manifest
- CI / acceptance checkpoint
- Drive artifact identity
- 历史阶段归档

`External_References` 用于源码级外部对标：

- `Notes/`：固定 `owner/repo@commit` 的源码学习记录与项目影响结论；
- `Snapshots/`：真正进入源码级研究后，对应精确 commit 的完整源码快照。

第三方源码快照必须记录固定 commit、license/NOTICE、快照 SHA-256、大小和 Drive File ID；同一 `owner/repo@commit` 已有经过验证的快照时应复用，不重复上传。当前五个 Foundation A 参考仓库的快照仍为 non-blocking pending，不得在未实际上传和核验前标记为已归档。

当前状态文档应原位更新并尽量复用 Drive File ID；历史 archive / freeze 仍保留，不因 CURRENT 更新而删除。

## 4. `01_Textbooks`

保存教材原始资产。

长期建议：

```text
01_Textbooks/
└── <course_id>/
    ├── Incoming/
    ├── Main/
    ├── Supplementary/
    ├── English/
    ├── Reference/
    └── Versions/
```

原则：

- 原始 PDF 不因结构化完成而删除。
- 同一本教材新版本不覆盖旧原件。
- 使用稳定 Drive file ID + hash + canonical book/version identity。
- App 不能只靠文件名判断教材身份。

每个导入文件至少记录：

```text
source_provider = google_drive
source_file_id
source_file_name
file_hash
course_id
book_id
book_version_id
imported_at
```

## 5. `02_Lectures`

保存 Learning 域课堂原始录音及必要的大型课堂附件。

未来建议按 course 和 profile 分隔：

```text
02_Lectures/
└── <course_id>/
    └── <profile_id>/
        ├── Audio/
        ├── Attachments/
        └── Processing/
```

录音处理层必须分开：

```text
raw_audio
raw_transcript
local_refined
ai_refined
```

当前产品决策：`raw_audio` 永久保留，派生稿不得覆盖原始音频或原始逐字稿。

## 6. `03_Exports`

保存从系统导出的结果，例如：

- 结构化教材导出包
- JSON / JSONL
- 题库导出
- ExamPoint / Exam Sprint 报告
- 章节总结
- 数据迁移包
- 用户主动导出的学习数据

同步内部增量包与用户导出包要在命名/metadata 上区分，避免误把运行队列当成正式用户导出。

## 7. `04_Backups`

保存阶段性备份，例如：

- 结构化数据库快照
- 发布前数据备份
- 教材映射表备份
- 迁移前备份
- 重要阶段的恢复包

备份和历史 evidence 不由普通同步任务自动删除或重写。

## 8. 未来多设备同步角色

最终目标：你和朋友都只使用 Book App 联网同步；朋友不需要进入 owner 的 Google Drive，也不持有 owner 的长期 Google 凭据。

推荐边界：

```text
你的 App ─┐
          ├─ Book Sync API ─→ owner-controlled Drive
朋友 App ─┘
```

Drive 是 Sync API 背后的文件/交换存储，不是让两台 App 同时直接打开同一个 SQLite 文件。

约束：

- 每台设备维护自己的本地 SQLite。
- 每台设备拥有稳定 `profile_id`。
- App/前端静态资源中不得嵌入 owner Drive Token、Google 密码、API secret。
- 朋友 App 只能访问 API 明确允许的共享数据。
- Meeting 私有数据不得进入朋友可读的 shared Learning response。

## 9. 增量同步，而不是整个 SQLite

未来同步采用 record/event increment。

概念流程：

```text
local SQLite mutation
        ↓
unique SyncEvent
        ↓
small incremental bundle
        ↓
Book Sync API / Drive
        ↓
remote app applies unseen event_id once
```

每个事件至少需要：

```text
event_id          // globally unique
profile_id
record_id
domain
record_type
revision
updated_at
operation
```

远端保存已应用 event identity，同一个事件重复下载也只执行一次。

音频等大文件不嵌入事件 bytes，只记录：

```text
file_id / audio_id
sha256
size
path-or-remote-reference
```

## 10. Future sync logical areas

实际目录名称在 Sync phase 实现时冻结；当前只固定逻辑边界：

```text
shared-learning/
├── incoming/<profile_id>/
├── processed/
└── manifests/

private/<owner_profile_id>/
└── meetings/
```

shared-learning 用于允许双方 App 同步的 Learning 数据。

private meeting 数据只能由 owner profile 的授权路径访问，不能因为共享同一个 Drive 项目根目录而自动下发给朋友。

## 11. 每日 `pending_ai` 精加工

未来录音在 App 本地先完成第一遍处理，再进入 Drive processing queue。

```text
recording
→ local first-pass
→ processing_status=pending_ai
→ Drive
```

第一版由 owner 每天晚上手动让 ChatGPT 处理当天全部新增录音，不做自动定时。

ChatGPT 处理时：

- Learning：读取 GitHub schema/rules + canonical 教材 + Drive 课堂数据，生成教材关联和 AI 精加工。
- Meeting：读取 private meeting 数据，生成摘要、Decision、ActionItem、Deadline、FollowUp。
- 完成后写回新 processing revision 并标记 `processed`。
- 已处理 revision 默认跳过，避免每日重复加工。

## 12. Learning 与 Meeting 的数据隔离

### Learning

可按后续共享规则参与你和朋友之间的同步。

课堂数据与教材仍保持：

```text
Textbook fact
Lecture fact
Derived / AI fusion
```

### Meeting

Meeting 是 Course / Book / Section 之外的独立私有域。

- 默认只属于 owner
- 不参与教材知识融合
- 不进入朋友 shared Learning feed
- 可复用录音/ASR/同步基础设施
- 原始 Meeting 录音同样永久保留

## 13. 隐私与凭据

当前产品决策：原始录音上传 Drive 前不要求 App 自行加密。

因此必须依赖：

- 正确的 Drive / API 访问控制
- shared / private 服务端数据隔离
- 不在 APK / browser JS 中嵌入长期秘密
- Drive 保持非公开

即使 Drive 文件被重命名或移动，也应尽量通过稳定 file ID + hash 识别。

## 14. 同步与去重

Book 项目继承全项目成果同步规则：

- 先对账，再写入
- 内容相同则 `SKIP_IDENTICAL`
- 同一逻辑 Drive 文件优先原位更新
- 历史 archive / freeze / snapshot 不自动去重删除
- 冲突标记 `CONFLICT_NEEDS_REVIEW`
- 没有变化时第二次同步应产生 0 个新 Git commit 和 0 个新 Drive object
