# Book Runtime Reference Layer

这里是 Book App / Course OS 的平台无关参考数据层。

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
LibraryRuntime
        ↓
SectionLearningRuntime
        ↓
Preview / Learn / Review / Practice
```

## 产品层规则

当前 Book App 的产品模型是：

```text
一个 App
├── 泛函分析课程 → 一本泛函分析教材
├── 实分析课程   → 一本实分析教材
├── 复分析课程   → 一本复分析教材
└── ...
```

也就是：

- App 可以包含多门彼此独立的教材课程；
- 当前产品入口要求每门课程恰好挂载一本 enabled 主教材；
- 新教材通过新增独立 course 并注册到 `library/library.json` 加入 App；
- 不在产品层合并不同教材的 Chapter / Section；
- `CourseRuntime` 仍保留通用多书挂载能力，但它只是底层兼容能力，`LibraryRuntime` 会拒绝多书 course 进入当前 App 产品入口。

## 运行时门

教材先运行：

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

时，正式学习入口才允许打开该教材。

`STRUCTURED_COMPLETE` 与 `RUNTIME_READY` 是两个独立门槛：结构化完成不等于已经具备正式运行时资产。

Functional Analysis v0.36 当前为 `STRUCTURED_COMPLETE / RUNTIME_READY`。

## 使用 BookRuntime

```python
from runtime import BookRuntime

book = BookRuntime.open("books/functional-analysis")

print(book.summary())
print(book.chapter_ids())

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

for chapter_id in course.chapter_ids():
    for section in course.sections_for_chapter(chapter_id):
        print(chapter_id, section.id, section.title_zh)
```

CourseRuntime 负责：

- course manifest 校验；
- enabled book 的 fail-closed readiness；
- 主教材 Chapter / Section 导航；
- 通用多书角色挂载兼容能力。

## 使用 LibraryRuntime

```python
from runtime import LibraryRuntime

library = LibraryRuntime.open("library")
print(library.summary())

for course_id in library.course_ids():
    course = library.course(course_id)
    print(course.course_id, course.main_book().book_id)
```

`LibraryRuntime` 是当前 Book App 的产品入口层：

- 使用显式 `library/library.json`，不做隐式文件夹发现；
- enabled course 按 `(order, manifest position)` 确定性排序；
- enabled course 必须能通过正常 `CourseRuntime.open()`；
- 当前产品 profile 要求 `len(course.book_ids()) == 1`；
- disabled 的未来课程不会被打开，也不会阻塞已有有效课程；
- catalog course path 必须保持在 repository root 内。

## 使用 SectionLearningRuntime

```python
from runtime import LibraryRuntime, SectionLearningRuntime

library = LibraryRuntime.open("library")
course = library.course("functional_analysis_course")
learning = SectionLearningRuntime.from_course(course, "ch01_s01")

source = learning.source()
preview = learning.preview()
learn = learning.learn()
review = learning.review()
practice = learning.practice()
```

### SectionLearningSource

`SectionLearningSource` 是四种模式共同依赖的教材证据层。它只投影已经由 `BookRuntime` 加载的内容，包括：

- canonical course / book / chapter / section identity；
- Section 页码范围；
- PageMap 边界；
- Section objects；
- 范围内 figures；
- translation batch 是否可用。

它不会重新解析 raw `*_structure.json`，也不会把 batch-level translation Markdown 猜测切成 Section 文本。

### 四种模式

Phase 1C 的四种模式是并列、独立、确定性的 source reference payload：

- **Preview**：Section 身份、对象类型索引、figure 和 translation 可用性；
- **Learn**：引用该 Section 当前全部 source objects / figures / translations；
- **Review**：仅引用 `definition / theorem / proposition / lemma / corollary / formula`；
- **Practice**：仅引用已有 `exercise / problem`。

如果 Review 或 Practice 没有匹配内容，会返回合法空列表，不会为了“看起来完整”而生成教材中不存在的内容。

所有 mode item 都通过：

```text
(kind, source_id)
```

回指 `SectionLearningSource`。Phase 1C 不生成 AI 总结、AI 解释、AI 题目或虚构教材锚点。

## 已实现能力

BookRuntime：教材身份/readiness、TOC、PageMap、历史结构归一化、objects/figures、translation、最终 search index。

CourseRuntime：Course → Book → Chapter → Section 运行时导航。

LibraryRuntime：一个 App 中多个独立教材课程的 catalog 与单书产品 profile gate。

SectionLearningRuntime：真实 Section 的来源证据投影，以及 Preview / Learn / Review / Practice 四个确定性入口。

## 测试

```bash
python -m unittest \
  tests.test_book_runtime \
  tests.test_course_runtime \
  tests.test_library_runtime \
  tests.test_section_learning_runtime -v
```

真实 Functional Analysis 验收保持：

- 8 Chapters；
- 132 Sections；
- 442 PageMap rows；
- 1493 unique final search records；
- `LibraryRuntime.open("library")` 成功；
- `SectionLearningRuntime.from_course(course, "ch01_s01")` 成功；
- Preview / Learn / Review / Practice 均可独立构建。

## 下一步

运行时合同稳定后，下一独立里程碑是 App UI shell：

```text
Library screen
→ Course screen
→ Chapter screen
→ Section screen
   ├── 预习
   ├── 学习
   ├── 复习
   └── 刷题
```
