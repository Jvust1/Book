# Book 数据模型基线

## 1. 设计原则

- 课程知识树独立于任何一本教材。
- 同一知识点跨教材复用稳定 `concept_id`。
- 教材版本、PDF 页、纸质页、内容锚点分离。
- 所有课堂结论、考点、题目和笔记尽量可回溯到原始来源。
- 任何版本更新都不能破坏已有学习记录。

## 2. 核心实体

```text
Course
CourseKnowledgeTree
Topic
Concept
ConceptRelation
Book
BookVersion
PageMap
Chapter
Section
ContentAnchor
Definition
Formula
Figure
Table
Example
Exercise
Question
Lecture
TranscriptSegment
LectureEvent
Exam
ExamScope
GradeRule
Note
Mistake
ReviewRecord
AnswerRecord
Mastery
AppProfile
StudyRecord
ExamPoint
ExamPointAnchor
```

## 3. Course

建议字段：

```text
course_id
name
term
language
status
main_book_id
created_at
updated_at
```

## 4. Book / BookVersion

```text
book_id
title
author
publisher
isbn
role                 // main / supplementary / english / reference
```

```text
book_version_id
book_id
version_label
file_hash
source_file_name
pdf_page_count
imported_at
supersedes_version_id
```

## 5. PageMap

用于解决 PDF 页码与纸质教材页码不一致问题。

```text
page_map_id
book_version_id
pdf_page_index
printed_page
printed_page_scheme   // arabic / roman / none / special
chapter_id
section_id
confidence
confirmed
```

## 6. ContentAnchor

稳定定位对象：

```text
content_anchor_id
book_version_id
chapter_id
section_id
pdf_page_index
printed_page
element_type          // paragraph / formula / figure / table / example / exercise
local_order
text_fingerprint
bbox                   // 可选，页内区域
```

版本更新时优先用 `text_fingerprint + 语义匹配 + 邻接结构` 重新定位，而不是依赖页码。

## 7. Chapter / Section

```text
chapter_id
book_version_id
number
title
start_pdf_page
end_pdf_page
start_printed_page
end_printed_page
```

```text
section_id
chapter_id
number
title
start_anchor_id
end_anchor_id
```

## 8. Concept

```text
concept_id
course_id
canonical_name
aliases
summary
difficulty
importance
status
```

教材中的具体出现位置通过中间关联表连接，不把教材位置直接写死在 Concept 上。

## 9. ConceptSource

```text
concept_source_id
concept_id
book_version_id
content_anchor_id
source_role           // definition / explanation / example / figure / formula
source_priority
```

## 10. Formula

```text
formula_id
concept_id
content_anchor_id
name
latex
symbols_json
assumptions_json
conditions_json
common_errors_json
```

## 11. Figure

```text
figure_id
content_anchor_id
figure_number
caption
asset_path
description
related_concept_ids
```

## 12. Table

```text
table_id
content_anchor_id
table_number
caption
image_asset_path
structured_data_json
```

## 13. Example / Exercise / Question

统一要求绑定知识节点。

```text
question_id
course_id
source_type            // textbook / teacher / ai_variant / exam / mistake
source_id
concept_ids
difficulty
question_type
stem
answer
explanation
content_anchor_id
```

## 14. Lecture

```text
lecture_id
course_id
sequence_number
date
started_at
ended_at
audio_asset_path
raw_transcript_status
refined_transcript_status
```

## 15. TranscriptSegment

```text
segment_id
lecture_id
start_ms
end_ms
raw_text
refined_text
confidence
speaker_label
```

必须保留 `raw_text`，精修稿不可覆盖原始稿。

## 16. LectureEvent

统一课堂关键事件：

```text
lecture_event_id
lecture_id
type
start_ms
end_ms
content
confidence
confirmed
linked_concept_ids
linked_anchor_ids
```

类型：

```text
IMPORTANT
EXAM
HOMEWORK
DEADLINE
SCOPE
GRADE_RULE
TEACHER_EXTENSION
TEXTBOOK_REFERENCE
QUESTION
```

## 17. GradeRule

```text
grade_rule_id
course_id
component              // homework / midterm / final / attendance ...
weight
source_lecture_event_id
confidence
confirmed
```

## 18. Exam / ExamScope

```text
exam_id
course_id
type                   // midterm / final / quiz
exam_date
confirmed
```

```text
exam_scope_id
exam_id
scope_type             // chapter / section / concept / excluded
reference_id
source_lecture_event_id
confidence
confirmed
```

## 19. ExamPoint

```text
exam_point_id
course_id
concept_id
title
priority_level         // S / A / B / C
priority_score
evidence_json
```

优先级证据可来自：

- 教材强调程度
- 老师强调次数
- 老师明确“会考”
- 作业频率
- 课堂练习频率
- 考试范围
- 用户错误率

## 20. ExamPointAnchor

这是“考点快速跳转”的关键表。

```text
exam_point_anchor_id
exam_point_id
anchor_type            // textbook / lecture / question
book_version_id
content_anchor_id
lecture_id
start_ms
question_id
label                   // 定义 / 公式 / 使用条件 / 例题 ...
sort_order
```

## 21. NavigationState

为了实现“一键返回且恢复原位置”，客户端保存：

```text
navigation_state_id
source_screen
source_entity_id
scroll_offset
expanded_items
filter_state
selected_tab
created_at
```

跳到教材、课堂或题目时将状态压入导航栈；返回时完整恢复。

当前 Web/PWA 的 Section / Search / QA 返回状态使用 `sessionStorage`，它只属于短期浏览恢复，不是长期学习事实。

## 22. AppProfile / StudyRecord

Phase 1G 已实现本机单用户身份与长期学习记录。首次初始化生成一个稳定、隐藏的 UUID `profile_id`，保存在本机 SQLite `app_profile` 单例记录中；当前没有账号选择 UI。

```text
AppProfile
profile_id              // stable hidden UUID
created_at
```

StudyRecord 实际持久化字段：

```text
study_record_id          // UUID
profile_id               // hidden local identity
course_id
book_id                  // server resolves canonical main book identity
section_id
mode                     // preview / learn / review / practice
status                   // in_progress / completed
progress                 // 0 / 100
started_at
last_studied_at
completed_at             // nullable
created_at
updated_at
revision                 // >= 1
deleted_at               // nullable; sync-ready tombstone field
sync_status              // Phase 1G 固定为 local
```

逻辑唯一键：

```text
(profile_id, course_id, section_id, mode)
```

当前语义：

- 四种模式并列、互不锁定、独立记录。
- 首次进入已成功加载的模式：`in_progress / progress=0`。
- 再次进入更新 `last_studied_at / updated_at / revision`。
- 手动完成：`completed / progress=100`。
- 已完成记录再次进入不会倒退；重复完成保持幂等，不制造 revision churn。
- `last_studied_at` 决定 recent learning。
- 浏览器不能提交或伪造 `profile_id` / `book_id`；`book_id` 由服务端通过 canonical Runtime 校验得到。
- 浏览器 DTO 不暴露内部 `profile_id / revision / sync_status`。
- SQLite 是 durable StudyRecord authority；`sessionStorage` 不是长期进度存储。

本地数据库路径由 `app/study/paths.py` 统一解析，并支持 `BOOK_APP_DATA_DIR` 覆盖。默认位置：Windows `%LOCALAPPDATA%/BookApp/book-app.sqlite3`，macOS `~/Library/Application Support/BookApp/book-app.sqlite3`，Linux/XDG `${XDG_DATA_HOME:-~/.local/share}/BookApp/book-app.sqlite3`。

## 23. Mastery

```text
mastery_id
user_id
concept_id
score
last_reviewed_at
correct_rate
mistake_count
review_count
status
```

状态可映射：未学习 / 已学习 / 初步理解 / 基本掌握 / 熟练 / 长期掌握。

`StudyRecord` 只表示学习行为，不等价于 `Mastery`。

## 24. Mistake

```text
mistake_id
user_id
question_id
concept_id
mistake_type
note
created_at
resolved_at
```

`mistake_type` 示例：

```text
CONCEPT
FORMULA
CALCULATION
MISREAD_CONDITION
CONFUSION
REASONING
CARELESS
```

## 25. 版本更新约束

新版教材进入时：

1. 新建 `BookVersion`
2. 重建 `PageMap`
3. 生成新版 `ContentAnchor`
4. 将旧锚点映射到新版锚点
5. 保留旧版锚点
6. 更新 `ConceptSource`
7. 不修改历史 `LectureEvent / Note / Mistake / StudyRecord`

这样历史记录始终可追溯。