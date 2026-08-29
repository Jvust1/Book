# Hybrid H0–H4a → Phase 1H Design

日期：2026-08-29

## 1. 背景与决策

Foundation A 已完成并合并。当前权威项目状态为 `POST_FOUNDATION_A_TRANSITION / READY_FOR_NEXT_PHASE_DESIGN`，下一阶段在实现新的架构子系统前必须先完成明确设计批准。

本设计记录 2026-08-29 已批准的混合路线：

```text
H0 → H1 → H2 → H3a → H4a → Phase 1H
```

该路线是对既有 Roadmap `Phase 1H → Foundation B` 的**经批准依赖例外**，不是对历史 Roadmap 的改写。目的在于先建立 identity / provenance / retrieval seam / Concept contract / shadow retrieval 这些兼容基础，再立即回到 Phase 1H 交付用户可见价值。

明确不在本设计授权范围内：

- H3b：真实生产 Concept 数据 authority / storage / generation / curation / provenance / revision lifecycle
- B4b：FTS / fusion / ranking 正式激活、权重与阈值
- B5：多教材公开消费、API/DTO/browser/session 协同迁移
- StudyRecord book-version migration

这些项目必须后续独立设计与批准。

## 2. 全局硬不变量

H0–H4a 以及 Phase 1H 必须共同遵守：

1. Golden Course 与 canonical `books/**` 不修改。
2. legacy `course.json` role 语义保持兼容；不要求旧 manifest 直接接受 canonical `primary`。
3. `main_book()`、现有单 enabled primary-book 产品 gate 与现有导航骨架保持不变。
4. Search / Source / QA 公开 DTO、HTTP JSON、浏览器 session state、provider payload 在 H0–H4a 中保持字面兼容。
5. Exact Search 评分、排序、过滤、错误语义保持不变。
6. QA 继续保留 independent `SourceResolver` canonical re-resolution、`EvidenceGate` 与 `CitationVerifier`。
7. StudyRecord schema、SQLite authority 与现有 identity 不在本路线中迁移。
8. H3a 不创建真实生产 Concept 数据。
9. H4a 不改变公开 Search/QA 排名，不与 StudyRecord DB 共库，不使用长期 shadow DB。
10. 不把 AI 生成内容作为教材事实。

Golden Course characterization baseline 继续为：

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

## 3. H0 — Neutral Book Identity Seam

### 3.1 目标

建立无副作用、stdlib-only 的中立 Book identity 层，使 `course_package` 与 Runtime 共享同一 canonical identity 规则，而不形成 producer/consumer 反向依赖。

推荐模块边界：

```text
book_core/
├── __init__.py      # 极薄、无副作用
└── identity.py
```

`book_core` 禁止反向 import `runtime` 或 `course_package`。

### 3.2 BookIdentity

内部 canonical identity：

```text
BookIdentity
├── book_id
├── logical_book_id
├── book_version_id
└── role
```

canonical role：

```text
primary
supplementary
reference
translation
```

legacy compatibility projection：

```text
main          → primary
supplementary → supplementary
reference     → reference
english       → translation
```

当前兼容规则固定为：

```text
logical_book_id = book_id
book_version_id = book_id + "@" + structured_version
```

H0 只增加 read-only identity projection，不迁移 legacy manifest。

### 3.3 兼容边界

以下保持原语义：

- `CourseBookEntry`
- `main_book()`
- `book_ids()`
- `books_by_role()`
- `CourseRuntime.summary()["books"]` 中的 legacy role
- enabled manifest order

legacy `course.json` 中 `role="primary"` 仍应保持 unsupported，直到未来 manifest evolution 被单独设计批准。

### 3.4 CI

因为仓库当前不是标准安装包，开发/CI/CLI 均以 repo root import 为当前合同。H0 必须补：

- `book_core` import/compile smoke
- Course Package FAST 对 `book_core/**` 的 path trigger
- Runtime workflow 对 `book_core/**` 的 path trigger
- App/UI workflow 对 `book_core/**` 的 path trigger

`course-package-heavy` 继续保持手工 `workflow_dispatch`，不增加自动触发。

## 4. H1 — Internal Source Provenance

### 4.1 SourceIdentity

内部 provenance 采用：

```text
SourceIdentity
├── course_id
├── book: BookIdentity
├── source_kind
└── source_id
```

核心 collision-safe key：

```text
(book_version_id, source_kind, source_id)
```

`section_id / chapter_id / source_anchor` 属于定位与上下文信息，不作为核心 source collision key。

### 4.2 公开序列化冻结

H1 的原则是：

```text
旧 DTO = 兼容层
新 identity/provenance = 内部事实层
```

内部字段不得因为 `dataclasses.asdict()` 或通用 JSON serialization 自动泄漏到：

- `SearchHit`
- `ResolvedSource`
- `EvidenceItem / EvidencePack`
- `QACitation`
- App DTO / HTTP JSON
- browser session state
- OpenAI-compatible provider payload

出口必须使用显式 allow-list projection；禁止“先序列化全部内部状态，再删除新字段”。

实施 H1 前必须补齐 Search 与 Source 正向 API exact-key characterization；QA exact-key contract 继续保持。Provider user/evidence payload 也必须补完整 exact-key freeze。

## 5. H2 — Shared Exact-only Retrieval Seam

### 5.1 目标

建立 Search 与 QA 共用的内部 Retrieval boundary，但不重写现有 Exact Search。

建议内部模块：

```text
runtime/retrieval.py
```

暂不加入 `runtime.__all__`，避免把内部 seam 过早升级为公共 Python API。

### 5.2 类型与角色

最小内部模型：

```text
RetrievalRequest
Retriever Protocol
RetrievalHit
RetrievalEngine
CanonicalExactRetriever
```

`CanonicalExactRetriever` 包装现有 `SearchRuntime`，将现有 `SearchHit` 显式转换为带 `SourceIdentity` 的 `RetrievalHit`。

H2 不做：

- score fusion
- normalization fusion
- FTS activation
- semantic retrieval
- cache
- process-global singleton

### 5.3 Search 数据流

```text
BookAppService.search()
↓
RetrievalEngine
↓
CanonicalExactRetriever
↓
existing SearchRuntime
↓
existing SearchHit
↓
internal RetrievalHit + SourceIdentity
↓
legacy Search projection
↓
existing API mapping
↓
same HTTP JSON
```

现有 Exact scoring、order、filter、limit、no-match 与 error semantics 必须完全保留。

### 5.4 QA 数据流与信任边界

```text
QARuntime
↓
EvidenceBuilder
├→ RetrievalEngine / CanonicalExactRetriever
└→ SourceResolver
↓
canonical EvidencePack
↓
EvidenceGate
↓
frozen provider projection
↓
Provider
↓
CitationVerifier
```

Retrieval 只负责“提出候选”；它不是教材事实 authority。

每个 QA candidate 必须继续通过 independent `SourceResolver` canonical re-resolution。`CitationVerifier` 继续独立复验，不能因为 Retrieval 已查过而省略。

### 5.5 DI 与错误

依赖注入保持 optional keyword-only，现有构造调用保持合法。默认 factory 产生 Exact-only engine；测试可以注入 fake/spy/failing retriever。

内部可定义：

```text
RetrievalQueryError
RetrievalUnavailableError
RetrievalInvariantError
```

但 App/HTTP 必须映射回当前稳定 status/code/中文 message。SourceIdentity 无法 round-trip 到 canonical source 时 fail closed，不能静默忽略后继续让模型回答。

H2 不新增 persistent retrieval cache，以保持当前加载/失败暴露时机并避免提前引入 stale 生命周期。

## 6. H3a — Concept / ConceptAlignment Contract Only

### 6.1 定位

H3a 只定义“什么叫合法 Concept 数据”，不决定真实生产 Concept 数据由谁生成、存在哪里、谁说了算。

纯 neutral contract 放在 `book_core`，并配套独立版本化 schema namespace，例如：

```text
book_core/concepts.py
schemas/concept-graph/v1/
```

### 6.2 Concept

建议最小结构：

```text
Concept
├── concept_id
├── title
├── aliases[]
├── prerequisite_concept_ids[]
└── provenance / revision metadata
```

`concept_id` 是课程知识 identity，不等于 `book_id`、`section_id` 或 `source_id`。

prerequisite edge 只存一个权威方向，dependent view 确定性派生，避免双写漂移。

Neutral validator 至少验证：

- schema/version
- required fields
- stable ID format
- duplicate concept/alignment IDs
- deterministic canonical serialization
- dangling Concept references
- duplicate edges
- self-loop
- relation enum
- provenance/revision/confidence shape
- cycle detection/reporting

H3a 暂不把 cycle 设为产品 hard-fail；是否强制 DAG 留到 H3b 根据真实数据决定。

### 6.3 ConceptAlignment

最小结构：

```text
ConceptAlignment
├── alignment_id
├── concept_id
├── book_version_id
├── section_id?
├── source_kind?
├── source_id?
├── relation
├── confidence?
├── revision
└── provenance
```

relation 第一版固定为：

```text
defines
explains
proves
examples
exercises
extends
contrasts
```

不加入模糊 `related_to` 语义垃圾桶。

### 6.4 两层验证

Neutral core 只验证与仓库无关的不变量，保持 stdlib-only。

Repository-bound `ConceptReferenceValidator` 可依赖 `CourseRuntime` / `SourceResolver`，验证：

- `book_version_id` 存在
- `section_id` 存在
- `source_kind/source_id` 可 canonical resolve

H3a 只提交 synthetic fixtures；不在 `books/**`、`courses/**`、`tests/golden/**` 或 `.build/**` 中创建真实 Functional Analysis Concept authority。

### 6.5 产品隔离

H3a 完成后 Search、QA、Preview、Learn、Review、Practice、Library、StudyRecord 都不读取 Concept。

删除 H3a artifacts 后产品行为应完全回到 pre-H3a 状态，无数据迁移。

Primary-book Section tree 继续是阅读/导航骨架；Concept Graph 以后只是知识关系骨架，不替代 Section。

## 7. H4a — Disposable Shadow FTS5 / BM25 Evaluation

### 7.1 定位

H4a 严格 shadow-only：

```text
public Search / QA
→ CanonicalExactRetriever only
```

影子评估单独运行：

```text
same query
├→ Exact
└→ ShadowFtsRetriever
      ↓
comparison report
```

FTS 结果不得进入用户 HTTP response 或 QA evidence。

### 7.2 Corpus

Shadow corpus 只来源于当前 canonical search-index candidate world，并且每条记录必须：

1. book identity 匹配；
2. 具备 H1 `SourceIdentity`；
3. 能通过 `SourceResolver` canonical round-trip。

无法回到 canonical source 的记录不能计入有效 shadow candidate。

### 7.3 存储与生命周期

允许：

```text
explicit temp dir
.build/retrieval-shadow/
```

禁止：

```text
books/**
courses/**
library/**
BOOK_APP_DATA_DIR/**
book-app.sqlite3
browser SQLite
```

Shadow DB 是 disposable derived artifact：missing / corrupt / stale 时只让 shadow unavailable，然后 rebuild，不建立 migration framework。

Index metadata 至少记录：

```text
book_version_id
source/package identity
corpus identity
index_schema_version
normalizer_version
builder_version
record_count
```

要求逻辑确定性，不要求两个 SQLite 文件 byte-for-byte 相同。

### 7.4 Query Normalizer

用户输入不能直接拼到 FTS `MATCH`。

必须经过独立、可测试的 normalization / tokenization / escaping，覆盖：

- 中英文
- punctuation
- quotes / colon / hyphen / asterisk
- FTS `AND / OR / NOT / NEAR` 等 reserved syntax
- Unicode / diacritics
- Hölder / Holder
- LaTeX / formula symbols
- parser-hostile input

异常输入最多导致 shadow zero-hit/unavailable，绝不能影响公开 Exact Search。

### 7.5 BM25 与比较报告

当前 Exact raw score 是 higher-is-better；SQLite FTS5 BM25 是 lower-is-better。H4a 不把两个 raw score 直接融合，只比较 rank 与候选集合。

固定 probe corpus 的 deterministic report 至少包含：

- Exact top-k
- FTS top-k
- top-k overlap
- FTS 新增 canonical candidates
- Exact zero-hit recovery
- provenance failures
- normalization behavior
- index/record counts
- stale/corrupt status
- diagnostic timing

Timing 不进入 deterministic report identity。

H4a 不设置未经 relevance truth 支持的 arbitrary recall/latency threshold，也不激活 ranking。是否启用 FTS/fusion 属于 B4b。

## 8. Phase 1H — User-visible Slices

完成 H0–H4a 后回到用户价值，顺序固定为：

```text
S1 Formula preview + recall
S2 Practice filters
S3 Deterministic flashcards
S4 Example/Object enhancement
S5 Review-duration presets
S6 Figure/Source metadata enhancement
```

### 8.1 S1 Formula

只使用现有 canonical formula fields。

Preview 提供公式摘要；Review 提供 hide → recall → reveal。不得用 LLM 重写公式事实。

### 8.2 S2 Practice Filters

在现有 exercise/problem/object metadata 上提供确定性筛选，例如按 object type 与当前 Section。

第一版不做 AI 难度预测、个性化推荐或错误率排序。

### 8.3 S3 Deterministic Flashcards

Flashcards 是 derived study view，不是新的教材事实。

只能由固定模板从 canonical `title/content/formula/object_type/number` 生成，并且相同输入得到相同卡片。

### 8.4 S4 Example/Object Enhancement

更好地组织现有 canonical definitions/theorems/examples/exercises/problems，并保留 number/title/source/page metadata。

Concept-aware 关系 UX 等 H3b。

### 8.5 S5 Review-duration Presets

支持确定性 1m / 5m / full（或等价）模式。Selection policy 必须写死并测试，不能由模型每次随机决定“什么最重要”。

### 8.6 S6 Figure/Source Metadata

使用现有 figure/source/page/source-anchor metadata 改善教材来源展示与回跳。

第一版不做 AI 自动读图、OCR 生成教材事实或自动图像解释。

### 8.7 Phase 1H 明确非目标

- Concept prerequisite / knowledge-path UX：等 H3b
- supplementary / translation / reference book public UI：等 B5
- FTS 影响真实 Search ranking：等 B4b
- notes / answers / mistakes / mastery：需要独立 local data model，不塞入 StudyRecord

## 9. TDD 与 Characterization Strategy

统一顺序：

```text
characterization GREEN
↓
new capability RED
↓
minimal implementation
↓
targeted GREEN
↓
relevant regression GREEN
```

旧的正确行为不为了“制造 RED”而故意改坏。先用 characterization test 锁住现状，再让新接口/新功能测试进入 RED。

### 9.1 H0 characterization

至少锁住：

- legacy role contract
- `main_book()` / order / summary compatibility
- Golden 8 / 132 / 1493 / 442 / 423
- Course Package generated-file set
- same-input deterministic package identity
- same-input generated file bytes

现有仓库没有提交固定 package hash 常量，因此 H0 如需 base characterization，应从批准的 base HEAD 生成 package outputs SHA-256 snapshot；不得凭空发明 hash。

### 9.2 H1 characterization

锁住：

- Search exact JSON key set
- Source exact JSON key set
- QA exact JSON/citation key set
- provider user/evidence payload exact key set
- browser QA/Search/Source session validators

### 9.3 H2 characterization

锁住：

- Exact scoring/order/filter/limit/no-match/errors
- Search/QA 均实际通过 shared Retrieval seam
- default adapter 与原 SearchRuntime projection 等价
- QA Section-first → book fallback
- EvidenceGate budgets/sufficiency
- independent SourceResolver/CitationVerifier
- stable App/HTTP error status/code/message/no-detail-leak

## 10. CI Design

### H0

`book_core/**` 变更必须触发：

- Course Package FAST
- Runtime reference tests
- App/UI tests
- import/compile smoke

### H1 / H2

重点 gate：

- exact serialization contracts
- Search regression
- QA evidence/citation regression
- browser session regression
- provider payload regression

### H3a

建立小型 Foundation-B Concept contract/reference gate；不要把 Concept-specific 逻辑塞回 Foundation A Course Package FAST。

### H4a

Shadow evaluator correctness 进 CI，但检索质量指标不是 activation gate。

### Phase 1H

每个 slice 跑 targeted Runtime/App/UI tests + relevant regression。

### HEAVY

`course-package-heavy` 继续保持手工 `workflow_dispatch`。只有真实执行后才能声称 HEAVY 已通过；存在 workflow 不等于已运行。

## 11. PR、Verification 与 Rollback Governance

### 11.1 PR 粒度

至少保持：

```text
H0 PR
H1 PR
H2 PR
H3a PR
H4a PR
```

Phase 1H S1–S6 进一步保持独立 reviewable slices。

每个 PR 都必须说明：

- 本 PR 的单一主要意图
- 修改范围
- 明确非目标
- targeted test evidence
- relevant regression evidence
- rollback 方法

### 11.2 Exact-HEAD

PR review / merge evidence 必须对应实际 PR HEAD。

如果 review 后新增 commit，旧测试证据不能继续冒充新 HEAD 证据，必须重新验证。

### 11.3 Merge

Book 默认分支保持保护：

```text
non-default branch
→ reviewable diff
→ PR
→ checks/review
→ explicit human merge authorization
→ merge
```

Agent 不自动 merge。批准本设计也不等于批准未来任何具体 PR merge。

现有 PR #15/#16 继续独立处理，不因本设计获批而自动合并。

### 11.4 Rollback

H0–H4a 硬要求：任何阶段回滚都不需要 canonical data migration。

- H0 可移除 identity seam/projection
- H1 可移除 internal provenance
- H2 可把 Search/QA consumer 接回 SearchRuntime
- H3a 删除 contract/schema/fixtures 后产品行为不变
- H4a 删除 shadow artifacts 并 rebuild，无 DB migration

Phase 1H S1–S6 也必须能独立撤回，不能靠修改 canonical books 或迁移 StudyRecord 才上线。

## 12. Governance Reconciliation

Foundation A merge 后已有少量 narrative docs 保留 pre-merge / Task-10 旧措辞。

本设计书面化并通过 review 后，可以在正常非默认分支/PR 中对以下文件做最小 current-state wording reconciliation：

```text
docs/CURRENT_STATE.md
docs/ROADMAP.md
docs/DEVELOPMENT_STRATEGY.md
```

只能修正客观过时措辞，并明确记录本 hybrid route 是 2026-08-29 新批准的 dependency exception；不得重写历史，让旧 Roadmap 看起来“一开始就是这条路线”。

## 13. Deferred Decisions — Hard Stops

### H3b

必须后续单独批准：

- production Concept authority
- storage location
- automated generation vs manual curation
- review workflow
- provenance/confidence semantics
- revision lifecycle
- multi-book conflict handling

### B4b

必须基于 H4a evidence 后续单独批准：

- 是否正式启用 FTS
- Exact/FTS fusion algorithm
- RRF/权重/策略
- query class routing
- acceptance thresholds
- activation rollback

### B5

必须后续单独设计：

- multi-book public API/DTO
- Search/Source/QA provenance exposure
- TypeScript types
- browser session migration
- source identity collision handling
- supplementary/reference/translation UX

当前 QA session validator 是 exact-key runtime validation，因此 additive citation fields 也可能破坏旧 session；B5 必须视为客户端+服务端+session-state 协同迁移，不允许仅靠后端追加字段上线。

### StudyRecord book-version migration

只有真实出现“同一用户记录需要区分教材版本”需求时再设计。不得预迁移。

## 14. Completion Definition

本路线完成需要同时满足架构基础与用户价值。

### 14.1 Architecture foundation

```text
[ ] H0 canonical BookIdentity seam 完成且 legacy compatibility GREEN
[ ] H1 collision-safe SourceIdentity 完成且所有外部 serialization freeze GREEN
[ ] H2 shared Exact-only Retrieval seam 完成且 Search/QA behavior-equivalent
[ ] H3a deterministic Concept/Alignment contract + reference validator 完成且产品未激活 Concept
[ ] H4a disposable shadow FTS evaluator 完成且 public Search/QA 仍 Exact-only
```

### 14.2 Phase 1H

```text
[ ] S1 formula preview/recall
[ ] S2 deterministic practice filters
[ ] S3 deterministic flashcards
[ ] S4 canonical example/object enhancement
[ ] S5 deterministic review-duration presets
[ ] S6 figure/source metadata enhancement
```

### 14.3 Regression / Governance

```text
[ ] Golden Course baseline 8/132/1493/442/423 unchanged
[ ] canonical books/** unchanged except separately approved content work
[ ] Search/Source/QA/provider/browser compatibility gates GREEN through H4a
[ ] relevant Runtime/App/UI regressions GREEN at exact reviewed HEADs
[ ] HEAVY only recorded if actually executed
[ ] every stage remains independently rollbackable
[ ] no automatic PR merge
[ ] H3b/B4b/B5/StudyRecord migration remain unimplemented unless separately approved
```

本路线完成后的稳定产品状态应为：

```text
single primary-book public experience
+ Exact-only public ranking
+ canonical textbook authority
+ no production Concept graph
+ no public multi-book
+ no StudyRecord version migration
```

同时用户已经获得 Phase 1H 的公式回忆、练习筛选、确定性卡片、对象学习增强、分时复习与来源导航能力。

## 15. Spec Approval Boundary

本文件固化的是已批准的第 1–7 节完整架构设计。

**本文件获用户书面 review/approval 之前，不进入 implementation plan。**

用户批准本文件后，下一步才允许调用 Superpowers `writing-plans`，把本设计拆成详细实施计划。该批准仍不等于批准任何具体实现 PR merge，也不授权 H3b、B4b、B5 或 StudyRecord book-version migration。