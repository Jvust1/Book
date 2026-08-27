# Book Runtime Reference Layer

这里是 Course OS 的平台无关参考数据层。

当前运行时链路：

```text
结构化教材资产
        ↓
Runtime readiness gate
        ↓
BookRuntime
        ↓
CourseRuntime
        ↓
Course / Book / Chapter / Section / Search / Anchor
```

## 运行时门

先运行：

```bash
python tools/check_runtime_readiness.py books/functional-analysis
```

需要刷新机器可读状态时：

```bash
python tools/check_runtime_readiness.py books/functional-analysis --write
```

只有输出：

```text
status = READY
```

时，正式学习软件才允许打开该书。

Functional Analysis v0.36 的最终运行时资产已经恢复并在 `main` 上通过校验，当前状态为 `READY`。`STRUCTURED_COMPLETE` 与 `RUNTIME_READY` 仍是两个独立门槛。

## 使用 BookRuntime

```python
from runtime import BookRuntime

book = BookRuntime.open("books/functional-analysis")

print(book.summary())
print(book.chapter_ids())

for section in book.sections_for_chapter("chapter_01"):
    print(section.number, section.title_zh)

for obj in book.objects_for_section("ch01_s01"):
    print(obj.type, obj.number, obj.name_zh, obj.anchor.pdf_page)

for hit in book.search("Hahn-Banach"):
    print(hit)
```

如果 readiness 不是 `READY`，默认会抛出 `BookRuntimeBlockedError`。仅恢复/诊断工具可以显式使用 `allow_blocked=True`；产品学习入口禁止绕过 gate。

## 使用 CourseRuntime

```python
from runtime import CourseRuntime

course = CourseRuntime.open("courses/functional-analysis")
print(course.summary())

book = course.main_book()
for chapter_id in course.chapter_ids():
    for section in course.sections_for_chapter(chapter_id):
        print(book.book_id, chapter_id, section.id, section.title_zh)
```

Phase 1B 规则：

- 一门课程可挂载多本 enabled 教材。
- 必须且只能有一本 enabled 主教材。
- 所有 enabled 教材都必须通过各自的 BookRuntime readiness gate；任一本失败时课程整体 fail-closed。
- Course 层 Chapter / Section 导航使用主教材已经加载的审计 TOC 顺序，并返回主教材 RuntimeSection 对象。
- 非主教材通过 `course.book(book_id)` 获取独立 BookRuntime。
- Phase 1B 不合并不同教材的章节命名空间。

## 已实现能力

BookRuntime：

- canonical `book_id` 一致性检查
- `STRUCTURED_COMPLETE` / metadata 页数一致性检查
- 双语 TOC 与 PageMap 读取
- 历史 structure schema 归一化
- Section 跨 batch 合并
- stable object ID 合并与冲突拒绝
- figure 归一化
- 中文学习层定位
- 最终 JSONL search index 流式读取
- 确定性中英关键词搜索
- PDF 页 → PageMap row 查询

CourseRuntime：

- course manifest 校验
- 多教材角色挂载
- enabled-book fail-closed readiness
- 主教材 Chapter / Section 导航
- 真实 Functional Analysis course fixture

## 测试

```bash
python -m unittest tests.test_book_runtime tests.test_course_runtime -v
```

真实 Functional Analysis fixture 的 CourseRuntime 验收覆盖：8 个 Chapter、132 个 Section、442 行 PageMap、1493 条最终搜索记录。

## 下一步

Phase 1B 合并后，下一独立里程碑是 Section 学习壳：

```text
Section
├── Preview
├── Learn
├── Review
└── Practice
```
