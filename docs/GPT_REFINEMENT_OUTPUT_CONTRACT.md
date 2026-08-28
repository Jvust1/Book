# GPT 精加工双输出契约

更新时间：2026-08-28
状态：APPROVED FUTURE CONTRACT

## 1. 目的

Book 的 Learning 课堂录音在每日 GPT 精加工后，不只生成一份完整结果，而是固定生成两套共享同一输入证据、处理版本和来源关系的输出：

```text
ProcessingJob
├── refined_full
└── refined_compact
```

该契约属于后续课堂智能结构化 / GPT Processing Job 阶段，不扩大当前 Phase 1G。

## 2. refined_full：完整精加工版

`refined_full` 是长期可追溯的完整派生知识结果，用于保留上下文、证据和后续重新加工能力。

至少可以包含：

- 老师课堂知识体系
- 完整术语与数学表达修正
- LectureEvent 与时间戳
- 老师强调、考点、考试范围、分值/占比、成绩规则
- 作业、Deadline、老师扩展
- `NO_PROOF_REQUIRED / NOT_EXAMINED / 了解即可` 等限制条件
- 与 Section / Concept / ExamPoint 的关联
- 主教材 / 辅助教材补充
- 定义、定理、公式、证明、例题、习题
- 来源锚点、置信度和 processing revision
- GPT 的组织、解释和学习建议

`refined_full` 不能覆盖 `raw_audio`、`raw_transcript` 或历史 processing revision。

## 3. refined_compact：精简学习版

`refined_compact` 用于日常快速查看，目标是“删废话，不删关键信息”。

默认优先保留：

```text
本节讲了什么
必须掌握
老师强调
考点
考试范围
分值 / 占比 / 成绩规则
定义 / 定理 / 公式
证明是否要求
作业 / Deadline
易错点
关键教材补充
```

默认应删除或高度压缩：

- 课堂寒暄
- 口头填充词
- 重复表达
- 与学习目标无关的闲聊
- 多次重复的同一例子
- GPT 套话、开场白和总结性废话
- 已由结构化字段完整表达的冗余说明

精简不能删除会改变知识或考试含义的限定条件，例如：

- 定理成立条件
- 公式适用条件
- 例外情形
- “不考 / 了解即可 / 不要求证明 / 只要求思路”
- 考试范围边界
- 分值、比例、日期和 Deadline
- 老师明确的否定或不确定表述

## 4. 生成顺序

禁止把 `raw_transcript` 直接交给一个自由摘要提示词后作为唯一精简结果。

标准链路：

```text
raw_audio / raw_transcript
        ↓
完整结构化精加工
        ↓
refined_full
        ↓
基于结构化字段的确定性保留规则
+ GPT 压缩表达
        ↓
refined_compact
```

因此 `refined_compact` 是 `refined_full` 的受约束派生视图，而不是另一份无来源的独立总结。

## 5. 版本与可追溯性

两套输出必须能够追溯到同一次 ProcessingJob。

建议至少保留：

```text
job_id
input_revision
processor_version
rule_version
output_schema_version
textbook_package_version
processed_at
refined_full_revision
refined_compact_revision
compact_source_full_revision
```

如果完整精加工结果重新生成，旧 compact 不应静默继续冒充最新结果；需要重新生成对应 compact revision，或明确标记 stale。

## 6. 来源规则

`refined_full` 和 `refined_compact` 都必须保持来源边界：

```text
Textbook fact
Lecture / teacher fact
Derived AI
```

精简版允许隐藏部分详细来源 UI，但底层引用关系必须仍然存在，并可从精简条目展开到：

- 老师原话 / 时间戳
- 主教材来源
- 辅助教材来源
- GPT 派生说明

教材补充不能在 compact 中被改写成老师说过的话。

## 7. App 展示原则

课堂精加工结果默认优先展示 `refined_compact`，降低阅读负担。

用户可以继续展开：

```text
精简版（默认）
├── 展开完整版
├── 查看老师原话 / 时间戳
└── 查看教材来源
```

完整版本始终保留，不能因为 App 默认展示精简版而被删除。

## 8. 与 What Changed 的区别

`refined_compact` 是“一次课堂/一次 ProcessingJob 的精简知识版本”。

`What Changed` 是跨 revision / 跨日期的增量变化摘要，例如：

- 今天新增了哪些知识点
- 考试范围发生了什么变化
- 新增了什么作业或 Deadline
- 哪些风险或 Mastery 状态发生变化

二者不能合并为同一个对象。

## 9. 验收约束

未来实现时至少测试：

1. 同一 ProcessingJob 同时产出 full + compact。
2. compact 可追溯到 full revision。
3. compact 不包含无意义寒暄和明显重复。
4. compact 不丢失考试范围、分值、Deadline、定理条件、例外和 proof requirement。
5. compact 中的教材补充不会伪装成老师原话。
6. full/compact 重跑产生新 revision，不覆盖 raw source。
7. App 默认 compact，但可无损展开 full/source。
8. 同步时 full 与 compact 有稳定 identity，可独立增量传输但保持 revision 关系。

## 10. 当前工程边界

当前唯一工程下一步仍然是：

```text
feature/study-record-phase-1g
→ StudyRecord + SQLite + hidden profile_id + recent learning + sync-ready metadata
```

本契约只冻结后续 GPT 精加工输出语义，不允许提前把 ProcessingJob、录音、Drive Sync 或课堂智能处理塞进 Phase 1G。
