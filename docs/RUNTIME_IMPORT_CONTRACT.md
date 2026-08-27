# Book Runtime Import Contract v0.1

## 目的

本契约定义“已完成结构化教材”进入 Course OS 软件运行时前必须满足的最小条件。目标是避免出现：结构化任务宣告完成，但仓库/Drive 副本缺少关键产物，软件仍误判为可学习状态。

## 1. 双状态模型

教材必须区分两个状态：

1. `STRUCTURED_COMPLETE`：结构化生产流程完成，审计 `FAIL = 0`。
2. `RUNTIME_READY`：当前软件可访问的位置中，运行时所需全部正式产物存在且互相一致。

`STRUCTURED_COMPLETE != RUNTIME_READY`。

只有两个状态同时满足，教材才可进入 Course OS 的正式学习入口。

## 2. 唯一事实源

运行时按以下顺序读取：

1. `STRUCTURED_COMPLETE.json`
2. `book_metadata.json`
3. `BOOK_AUDIT_REPORT.md`
4. `toc_bilingual.json`
5. `page_map.csv`
6. 全部结构化批次 `*_structure.json`
7. 与结构批次对应的中文学习层 `*_translation_zh.md`
8. `search_index_<final_version>.jsonl`
9. `qa_retrieval_policy.json`

不得用旧的 `next_action`、旧 delta search index、旧 partial translation 或 README 进度替代最终事实源。

## 3. 完成标记校验

`STRUCTURED_COMPLETE.json` 至少包含：

```json
{
  "status": "STRUCTURED_COMPLETE",
  "book_id": "...",
  "pdf_pages": 0,
  "printed_final_page": 0,
  "version": "...",
  "audit_fail_count": 0,
  "audit_report": "BOOK_AUDIT_REPORT.md",
  "search_index": "search_index_....jsonl"
}
```

硬门槛：

- `status == STRUCTURED_COMPLETE`
- `audit_fail_count == 0`
- `pdf_pages == book_metadata.pdf_total_pages`
- `book_id == book_metadata.book_id`
- `qa_retrieval_policy.book_id == book_metadata.book_id`
- `audit_report` 文件存在
- `search_index` 文件存在

任一失败：`RUNTIME_READY = false`。

## 4. PageMap 校验

运行时必须依赖 `page_map.csv`，不得只使用固定偏移公式。

最低校验：

- 文件存在。
- 物理 PDF 页覆盖数等于 `pdf_total_pages`。
- `pdf_page_index` 不重复。
- PDF 页连续。
- printed page 可为空，但存在时必须可解析。
- 章节/节定位不得把 PDF 页和纸质页混为同一字段。

固定偏移只能作为诊断提示，不能作为唯一事实源。

## 5. TOC 校验

`toc_bilingual.json` 必须存在，并能够形成：

```text
Book
└── Chapter
    └── Section
        └── Subsection
```

运行时至少需要稳定的 chapter/section ID、编号、英文标题、中文标题和页范围。

## 6. Structure batch 校验

结构化批次允许历史上存在不同 schema，但 loader 必须归一化到统一对象。

目前已观察到两类输入：

### Frontmatter schema

典型字段：

```text
chunk_id
pdf_pages
page_labels
content_units[]
```

### Main text schema

典型字段：

```text
chunk_id
parent_storage_chunk
pdf_pages
printed_pages
chapter_id
sections[]
key_objects[]
figure_anchors[]
translation_status
```

运行时不得要求所有历史 chunk 原始 JSON 完全同 schema；应先 adapter，再生成统一 runtime model。

### 统一 RuntimeStructureBatch

建议输出：

```text
batch_id
pdf_page_start
pdf_page_end
printed_page_start
printed_page_end
chapter_ids[]
sections[]
objects[]
figures[]
continuation_edges[]
source_file
translation_file
```

## 7. Stable ID 与 continuation

所有 theorem / proposition / lemma / definition / concept / exercise 等对象必须保留稳定 ID。

启动校验：

- 不允许冲突型重复 ID。
- continuation 引用必须指向存在的 batch。
- `continues_in` / `continued_from` 必须能够闭合。
- 历史旧 ID 不得重新生成第二身份。

## 8. 中文学习层

正式完成教材要求每个结构批次存在非空中文学习层。

运行时规则：

- `*_translation_zh_partial.md` 不可作为正式完成版本。
- 文件名包含 `partial` 或结构状态仍标记 translation partial 时，readiness 校验必须报告。
- 允许“非逐句直译”，但不得缺失完成审计要求的定义、定理、公式条件和证明逻辑学习层。

## 9. 搜索索引

正式运行时只读取 `STRUCTURED_COMPLETE.search_index` 指向的最终合并索引。

禁止：

- 把多个 `search_index_delta_v*` 在客户端临时拼接后冒充最终索引。
- 在最终索引缺失时静默降级为“已完成搜索”。

可允许开发模式 fallback，但 UI 必须显示 `DEGRADED`，不能显示正式可用。

最终 index 每条记录至少应支持：

```text
object_id
object_type
book_id
chapter_id / section_id
pdf_page
printed_page
source_anchor
bilingual searchable text / aliases
```

## 10. QA policy

教材问答必须：

- 优先结构化来源。
- 返回 `source_anchor`。
- 返回 jump target。
- 不得发明缺失结构。
- 只有明确标记时才使用 raw PDF fallback。

`qa_retrieval_policy.book_id` 必须与 canonical `book_id` 一致。

## 11. Runtime readiness 输出

每本书建议生成：

`RUNTIME_READINESS.json`

格式：

```json
{
  "status": "READY | BLOCKED | DEGRADED",
  "book_id": "...",
  "structured_version": "...",
  "checks": [],
  "missing_required_files": [],
  "stale_files": [],
  "identity_mismatches": [],
  "next_action": "..."
}
```

软件只在 `status == READY` 时开放正式学习入口。

## 12. Functional Analysis v0.36 当前 fixture

Canonical book ID：

`stein_shakarchi_functional_analysis_2011`

已确认：

- `STRUCTURED_COMPLETE.json`：存在，v0.36，442 页，FAIL=0。
- `book_metadata.json`：存在。
- `BOOK_AUDIT_REPORT.md`：存在，PASS 20 / WARN 1 / FAIL 0。
- 43 个结构批次在审计中被确认完整。
- `qa_retrieval_policy.json` 已统一到 canonical book ID。

当前 GitHub 副本阻塞：

- `page_map.csv` 缺失。
- `toc_bilingual.json` 缺失。
- `search_index_v0_36.jsonl` 缺失。
- `chunks/chunk_002_translation_zh_partial.md` 仍残留，且对应 structure 仍带旧 partial 状态。
- 审计报告描述的最终修复产物与当前 GitHub 工作树没有完全同步。

因此当前应判定：

`STRUCTURED_COMPLETE = true`

`RUNTIME_READY = false`

在最终 v0.36 导出产物同步前，不应开始构建依赖这些缺失文件的正式 Section/Search/QA 数据层。

## 13. 下一步

1. 找回/重新同步 v0.36 FINAL 导出包。
2. 将最终 `page_map.csv`、`toc_bilingual.json`、`search_index_v0_36.jsonl`、修复后的 chunk_002 学习层与结构状态同步到 GitHub/Drive。
3. 运行 readiness 校验直到 `READY`。
4. 再实现 `Course → Book → Chapter → Section` loader。
