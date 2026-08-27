# Book Runtime Reference Layer

这里是 Course OS 的平台无关参考数据层。

当前目标不是绑定最终前端技术栈，而是先固定：

```text
结构化教材资产
        ↓
Runtime readiness gate
        ↓
BookRuntime
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

当前 Functional Analysis v0.36 因最终运行时产物没有完整同步，预期为 `BLOCKED`。这与教材已经 `STRUCTURED_COMPLETE` 不矛盾。

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

如果 readiness 不是 `READY`，默认会抛出 `BookRuntimeBlockedError`，不会静默使用旧索引、partial 中文层或猜测的 PageMap。

仅恢复/诊断工具可以显式：

```python
book = BookRuntime.open("books/functional-analysis", allow_blocked=True)
```

产品页面禁止使用这个参数绕过 gate。

## 已实现的归一化

- canonical `book_id` 一致性检查
- `STRUCTURED_COMPLETE` / metadata 页数一致性检查
- 双语 TOC 读取
- PageMap CSV 读取
- 递归发现历史 `*_structure.json`
- 兼容 early frontmatter `content_units[]` schema
- 兼容 main-text `sections[] + key_objects[]` schema
- Section 跨 batch 合并
- stable object ID 合并与冲突拒绝
- 按 anchor page 将对象归入最具体 Section
- figure 归一化
- 中文学习层定位（拒绝 partial 文件）
- 最终 JSONL search index 流式读取
- 简单确定性中英关键词搜索接口
- PDF 页 → PageMap row 查询

## 测试

```bash
python -m unittest tests.test_book_runtime -v
```

测试包含：

1. 当前 Functional Analysis fixture 在缺最终产物时必须被 gate 阻止。
2. 完整最小 fixture 可以成功加载 Section、对象、PageMap 和 search index。

## 下一步

Issue #2 完成后：

1. `RUNTIME_READINESS` 变为 `READY`。
2. 用真实 Functional Analysis v0.36 跑 BookRuntime 全量加载。
3. 核对 8 个 Chapter、全部 Section、stable objects 和 1493 条最终搜索记录。
4. 在此接口之上实现 `CourseRuntime`。
5. 再接正式 UI 的 `Course → Book → Chapter → Section`。
