# Foundation A — Course Package Contract / Golden Course Design

日期：2026-08-28

## 1. 目标

Foundation A 的目标是建立 Book 从当前可运行的 Course Runtime 走向标准 Course Package 驱动 Course OS 的稳定基础。

本阶段必须做到：

1. 冻结统一、版本化、机器可验证的 Course Package Contract。
2. 将 Stein & Shakarchi《Functional Analysis》固化为 Golden Course。
3. 建立 canonical identity / source integrity / package determinism 自动验收。
4. 建立第一批 Architecture Fitness Functions。
5. 为 FAST / PR FULL / HEAVY 分层 CI 建立明确职责。
6. 保持 Phase 1A–1G 当前 Runtime / API / App 行为兼容。

本阶段不以新增用户界面为目标。

核心原则：

```text
App 通用，教材是数据。
Package 描述并验证 canonical 教材，
不得为了 Package 反向改写 canonical 教材。
```

## 2. 非目标

Foundation A 第一阶段明确不实现：

- PDF → AI 自动结构化
- 真正的多教材 App UI
- Concept Graph / ConceptAlignment
- Unified Retrieval
- ExamPoint
- Lecture / ASR
- Drive Sync
- Android
- App 改为直接消费 Course Package
- 将所有 canonical Book 数据复制成新的巨大 Package

真正的“上传资料 → 结构化”Compiler 流程等 Contract 稳定后再实现。

## 3. 当前兼容边界

现有系统继续保留：

```text
courses/<course>/course.json
books/<book>/
runtime/BookRuntime
runtime/CourseRuntime
runtime/LibraryRuntime
```

现有 `course_manifest_v1` 和 Runtime 仍然是产品运行路径。

Foundation A 新增的 Course Package 是一层：

```text
validation / inventory / identity / release contract
```

而不是立刻替换 Runtime。

因此 Foundation A 完成后：

```text
现有 App
→ 仍走现有 Runtime

Course Package
→ 用于 compile / validate / Golden regression / 后续迁移
```

历史规划中曾把未来统一课程包泛称为 “Course Package v2”。本设计中的 `course_package_v1` 指**第一版正式、机器可验证的 Course Package Contract schema**，不是对现有 `course_manifest_v1` 的版本号延续，也不表示产品路线倒退。

## 4. Canonical Book Role

新的 Course Package canonical role 只有：

```text
primary
supplementary
reference
translation
```

规则：

- 一个可注册 Course 必须恰好有一个 enabled `primary`。
- `primary` 决定第一阶段 Course 的 Chapter / Section 阅读骨架。
- supplementary/reference/translation 保持自己的 Book identity 与 source provenance。
- Package 不融合不同 Book 的正文、页码、证明或编号。

兼容旧 `course_manifest_v1` 时：

```text
main → primary
supplementary → supplementary
reference → reference
english → translation
```

legacy role 只允许出现在 Compiler 输入适配层，不进入新的 canonical Package schema。

## 5. Course Package v1

建议逻辑结构：

```text
course-package/
├── course_package.json
├── books.json
├── artifacts.json
├── chapters.json
├── sections.json
├── readiness.json
└── package.sha256
```

第一版不复制 `books/<book>/**`。

Package 中通过 repository-relative canonical path + SHA-256 指向现有资产。

### 5.1 `course_package.json`

至少包含：

```text
schema_version
package_version
course_id
course_name
language
primary_book_id
books
chapter_count
section_count
search_record_count
package_identity
readiness
```

禁止把随机 UUID、当前时间或机器路径放入 `package_identity`。

### 5.2 Book entry

每个 Book 至少包含：

```text
book_id
logical_book_id
book_version_id
role
canonical_path
enabled
required
structured_status
structured_version
runtime_status
pdf_page_count
printed_final_page
content_identity
```

当前历史教材若暂时没有独立 `logical_book_id / book_version_id`，Compiler 可以通过明确、确定性的兼容规则生成，但规则必须固定并测试。

不得将环境绝对路径写入 Package。

## 6. Artifact Inventory

`artifacts.json` 描述 Package 所依赖的 canonical artifacts。

每项至少：

```text
artifact_type
relative_path
sha256
size_bytes
required
book_id
```

首批 artifact 类型包括：

```text
book_metadata
structured_complete
audit_report
toc
page_map
search_index
qa_policy
structure
readiness
```

Package validator 必须验证：

- 文件存在
- 路径没有逃逸 repository/package boundary
- SHA-256 匹配
- identity 匹配
- required artifact 不缺失

Artifact Inventory 是“引用 canonical 事实”，不是“复制 canonical 事实”。

## 7. Deterministic Package Identity

Course Compiler 相同输入必须产生相同 package identity。

Package identity 定义为：

```text
SHA-256(
  canonical_json(
    schema_version
    + package_version
    + course identity
    + normalized book entries
    + normalized artifact inventory hashes
    + structural baseline
  )
)
```

canonical JSON 必须：

- key 排序固定
- UTF-8
- 数字/布尔值规范化
- 不包含生成时间
- 不包含本机绝对路径
- 不包含临时目录

允许在非 identity metadata 中记录 `generated_at`，但它不得影响 Package identity。

连续 compile 两次：

```text
same source → same package_identity
```

是 Foundation A 的硬 gate。

## 8. Course Compiler v1 职责

第一版 Compiler 仅负责把**已经结构化完成的 Course / Book**编译成标准 Package。

流程：

```text
course.json
+ canonical Book assets
↓
legacy manifest normalization
↓
Book readiness validation
↓
identity validation
↓
artifact discovery
↓
SHA-256 inventory
↓
structural baseline extraction
↓
Course Package
↓
Package validator
```

Compiler v1 不负责：

```text
raw PDF parsing
OCR
AI extraction
Concept generation
ExamPoint generation
ASR
```

这些属于后续 Compiler pipeline stages。

## 9. Readiness Contract

Package readiness 使用：

```text
PASS
WARN
FAIL
```

### PASS

所有 required identity、artifact、hash、source、structural gate 均通过。

### WARN

Package 可以安全使用，但存在非阻塞诊断，例如 legacy compatibility alias。

### FAIL

存在任何会破坏可信使用的错误，例如：

- canonical identity mismatch
- required artifact missing
- hash mismatch
- primary book 数量不等于 1
- PageMap 不连续
- required source anchor 缺失
- search index identity 错误
- Package path escape
- Package schema invalid

`FAIL` Package 不得注册进入正常 Library Runtime。

## 10. Golden Course

Functional Analysis 正式作为 Golden Course。

固定 baseline：

```text
course_id: functional_analysis_course
book_id: stein_shakarchi_functional_analysis_2011
chapters: 8
sections: 132
search_records: 1493
pdf_pages: 442
final_printed_page: 423
structured_status: STRUCTURED_COMPLETE
runtime_status: READY
```

Golden Course gate 必须验证：

1. Course identity。
2. Book identity。
3. Chapter count。
4. Section count。
5. Search record count。
6. PDF page count。
7. PageMap 连续性。
8. source anchor 完整性。
9. required canonical artifact hash/inventory。
10. Compiler deterministic identity。
11. Package validator PASS。
12. Existing BookRuntime/CourseRuntime 仍能正常加载。

严禁为了让 Golden test 变绿而修改教材事实。

## 11. Canonical Asset Protection

Foundation A 必须加入可执行保护。

Compiler / validator 在默认模式只能读取：

```text
books/**
courses/**
```

输出必须进入独立 build/temp 路径，例如：

```text
.build/course-packages/<course_id>/
```

不得：

- 修改 `books/functional-analysis/**`
- 自动写 `RUNTIME_READINESS.json` 到 canonical Book
- 为测试修正教材正文
- 自动覆盖 source map
- 修改 PageMap
- 修改 search index

测试应对 Foundation A diff 建立 canonical-zero-mutation gate。

## 12. Schema Authority

Foundation A 首批建立 JSON Schema 权威来源：

```text
schemas/course-package/
├── course-package-v1.schema.json
├── books-v1.schema.json
├── artifacts-v1.schema.json
└── readiness-v1.schema.json
```

原则：

```text
Schema
↓
Compiler output
↓
Validator
↓
tests
```

暂时不要求重写全部现有 Pydantic / TypeScript contract。

后续 API migration 才逐步由 OpenAPI / JSON Schema 自动生成前后端 contract。

## 13. Architecture Fitness Functions — Foundation A 首批

第一批至少自动检查：

1. Browser source 不直接访问 SQLite。
2. canonical `books/**` 不被 StudyRecord / Compiler 写入。
3. Course Package 不含系统绝对路径。
4. Course Package 不含 API key/token/secret 字段。
5. Package 只能引用 repository boundary 内 canonical artifacts。
6. 一个 Course 恰好一个 primary。
7. Package artifact hashes 必须匹配。
8. Package identity 必须 deterministic。
9. Golden Course canonical identity 不得漂移。
10. 当前 Phase 1A–1G Runtime/App contract 不因 Foundation A 回归。

其余 raw_audio、Meeting、Sync 等 fitness function 在对应功能进入代码库后再开启强制 gate。

## 14. CI 分层

### FAST

用于普通开发的快速反馈：

```text
schema validation tests
compiler unit tests
package validator tests
architecture static checks
targeted Runtime tests
```

### PR FULL

PR 合并前：

```text
FAST
+ Python full Runtime
+ App/API
+ SQLite
+ Vitest
+ TypeScript
+ Vite build
+ Golden Course compile/validate
+ Chromium acceptance
```

### HEAVY / RELEASE

仅在教材重编译、Package release 或重大 contract migration：

```text
canonical rebuild validation
full artifact hash reconciliation
Golden Course deep integrity
release Package build
larger compatibility matrix
```

不应让每次小改动重复执行不必要的原始教材重建。

## 15. Error Handling

Compiler / validator 必须 fail closed。

错误至少分：

```text
schema_error
identity_error
artifact_missing
artifact_hash_mismatch
path_escape
book_not_ready
structural_baseline_mismatch
package_nondeterministic
```

错误信息可以包含 repository-relative path，但不得在用户/API 输出中泄露：

- secret
- token
- provider credential
- 不必要的本机私人绝对路径

## 16. Migration Strategy

Foundation A 不一次性迁移 App。

顺序固定：

```text
A1 Contract + Validator
↓
A2 Golden Course Package
↓
A3 Architecture Fitness
↓
A4 CI layering
↓
A5 Compiler v1
↓
contract stable
↓
后续 Runtime consumer migration
↓
真正多教材 runtime
```

只有 Package v1 经 Golden Course 持续验证稳定后，才讨论让 `CourseRuntime` 或 App 直接消费 Package。

## 17. 验收标准

Foundation A 第一阶段完成必须满足：

```text
[ ] Course Package v1 JSON Schema 已冻结
[ ] legacy course_manifest_v1 可确定性规范化
[ ] Functional Analysis 可成功 compile
[ ] Package validator = PASS
[ ] 两次 compile package_identity 完全一致
[ ] Golden baseline 8 / 132 / 1493 / 442 全通过
[ ] canonical books/functional-analysis/** 零修改
[ ] path escape / hash mismatch / identity mismatch 都有 RED→GREEN tests
[ ] Architecture Fitness 首批 gate 通过
[ ] Runtime full regression PASS
[ ] App full regression PASS
[ ] Web/typecheck/build PASS
[ ] real Chromium PASS
```

Foundation A 不以“生成了一个 JSON 文件”作为完成标准，而以：

```text
稳定 Contract
+ deterministic Compiler
+ Golden Course
+ executable architecture gates
+ full regression
```

作为完成标准。
