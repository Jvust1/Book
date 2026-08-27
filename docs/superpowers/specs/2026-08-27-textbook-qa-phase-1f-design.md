# Phase 1F 教材内问答设计

> 日期：2026-08-27
> 状态：待用户审阅
> 设计分支：`design/textbook-qa-phase-1f-v2`
> 基线：`main@7e191693cd84174b2229337e411bcd44dde68612`（Phase 1E 已合并）
> 设计原则：严格教材内回答、来源可追溯、模型不可伪造教材身份、local-first、会话态不等于长期学习记录

## 1. 目标

Phase 1F 在 Phase 1E 已完成的确定性教材搜索与 SourcePage 往返能力之上，增加“教材内问答”。

本阶段的核心交付不是“让模型能生成文字”，而是建立一条可验证的教材证据链：

```text
用户问题
→ 当前 Section 优先检索
→ 必要时扩大到当前教材全书
→ SearchRuntime
→ SourceResolver
→ EvidenceBuilder
→ 服务器 EvidenceGate
→ ModelProvider
→ 模型结构化 JSON
→ CitationValidator
→ 真实教材 Citation DTO
→ SourcePage
```

最终产品保证：

1. 第一版只允许依据当前 course 的 enabled 主教材回答。
2. 模型自身知识不能作为教材答案的事实来源。
3. 所有展示为“教材回答”的关键结论必须有本轮真实教材 evidence 支撑。
4. 模型只能引用服务器预先分配的 `evidence_id`，不能创建 `source_id`、页码、anchor 或 URL。
5. 证据不足时明确拒答，而不是用模型常识补齐。
6. 模型生成内容永远是“AI 生成回答”，绝不写回教材正文。
7. Course 页和 Section 页均可进入问答，并共享当前 course 的短期 QA 会话。
8. QA → Source → Return 必须恢复问答上下文和滚动位置，不因查看教材来源产生第二套状态体系。

## 2. 已确认的产品决策

Phase 1F v1 固定采用以下决策：

- **回答知识范围**：仅当前教材，不允许“教材 + 模型自身知识”。
- **检索范围**：从 Section 页提问时“当前 Section 优先，证据不足再扩展到全书”；从 Course 页进入时直接全书检索。
- **回答长度**：自动按问题类型选择 `brief / explain / compare / proof`。
- **连续追问**：支持当前浏览器会话内连续问答；不做长期 QA 历史。
- **入口**：Course 页和 Section 页都有入口，共用同一个 course QA session。
- **模型位置**：在线模型；完整教材留在本机，只发送当前问题、有限近期对话和小型 EvidencePack。
- **密钥位置**：仅本机 Python/FastAPI 侧读取，前端不可见。
- **Provider**：第一版实现一个 OpenAI-compatible Provider；内部保持 `ModelProvider` 抽象，未来可增加 Ollama/local provider。
- **模型输出**：严格结构化 JSON。
- **引用机制**：模型只能返回本轮 `evidence_id`。
- **证据充分性**：服务器最低门槛 + 模型 `insufficient_evidence` 二次判定；任一方判不足都不输出确定性教材答案。
- **CI**：不调用真实收费 API，使用 deterministic fake provider 完成 Runtime/API/Web/Playwright 验收。

## 3. 非目标

Phase 1F 明确不做：

- 跨 course / 跨教材问答；
- 使用模型外部知识补教材内容；
- Web 搜索或联网资料补充答案；
- embedding、向量数据库、reranker；
- 将 QA 历史写入长期数据库或 StudyRecord；
- 把生成回答写入 `books/**`、课程结构或教材正文；
- 让模型直接读取仓库、文件系统、GitHub、Drive 或任意本地文件；
- 模型自主工具调用；
- 同时实现多个在线 Provider；
- Ollama/local model 实现；
- 原始 PDF Reader；
- 将 `qa_retrieval_policy.json` 中的 raw-PDF fallback 作为当前核心路径。

当前 Functional Analysis Runtime 已为 READY，结构化教材是 Phase 1F 的唯一正式证据源。`qa_retrieval_policy.json` 中的 raw-PDF fallback 仍保留为未来扩展约定，但本阶段不启用，也不为 QA 伪造缺失 anchor 或结构。

## 4. 架构与信任边界

### 4.1 总体架构

```text
React / PWA
   ↓ typed HTTP
FastAPI
   ↓
BookAppService
   ↓
QARuntime
   ├─ SearchRuntime
   ├─ SourceResolver
   ├─ EvidenceBuilder
   ├─ EvidenceGate
   └─ ModelProvider
          ↓
   Provider JSON
          ↓
   CitationValidator
          ↓
      QAResult
          ↓
BookAppService DTO
          ↓
React QAPage
```

### 4.2 决定性与非决定性边界

以下部分必须完全确定、无需真实模型即可测试：

- course / book 选择；
- question / section / history 输入校验；
- Section 优先与全书 fallback；
- SearchRuntime 检索；
- SourceResolver 二次解析；
- EvidencePack 构造；
- EvidenceGate；
- evidence ID 分配；
- provider JSON schema 校验；
- citation 验证；
- QA DTO 投影；
- sessionStorage 状态；
- SourcePage 往返。

只有“答案措辞与解释组织”允许由模型产生。

## 5. `QARuntime`

建议新增：

- `runtime/qa_runtime.py`
- `runtime/qa_models.py`
- `runtime/qa_evidence.py`
- `runtime/qa_provider.py`

`QARuntime` 是教材证据与模型生成之间的核心 trust boundary。

建议公开入口：

```python
QARuntime.from_course(course: CourseRuntime, provider: ModelProvider) -> QARuntime

QARuntime.answer(
    question: str,
    *,
    section_id: str | None = None,
    history: Sequence[QAHistoryMessage] = (),
) -> QAResult
```

规则：

- `question.strip()` 后不能为空；
- 首版问题最大 1000 Unicode code points；
- `section_id` 为可选 canonical Section ID；
- 非空 `section_id` 必须属于当前 course 主教材；
- `history` 只允许 `user / assistant` 文本消息；
- history 只能用于理解追问语义，永远不能成为教材 evidence。

## 6. 检索范围：Section 优先 → 全书 fallback

### 6.1 从 Section 页提问

当请求带 `section_id`：

```text
question + section_id
↓
Section-scoped retrieval
↓
SourceResolver
↓
EvidenceGate(section)
├─ 通过 → scope_used = section
└─ 不通过
    ↓
    book-scoped retrieval
    ↓
    SourceResolver
    ↓
    EvidenceGate(book)
    ├─ 通过 → scope_used = book
    └─ 不通过 → insufficient_evidence
```

“扩展到全书”不是把本节证据丢弃。最终 book EvidencePack 可保留本节高相关证据，并补入其他章节来源；前端明确显示“本节 + 教材其他章节”。

### 6.2 从 Course 页提问

`section_id = null` 时：

- 不进行伪 Section 检索；
- 直接使用当前 course 主教材全书范围；
- `scope_requested = book`；
- `scope_used = book`。

### 6.3 SearchRuntime 复用原则

Phase 1F 不建立第二套搜索索引。

实现应复用 Phase 1E 的 audited `SearchRuntime`。若 Section 优先需要新增 scope 能力，应采用**向后兼容的 additive filter**，并保证：

- 未传 Section 时 Phase 1E 既有搜索结果与排序不变；
- scope 过滤发生在最终 evidence limit 截断之前，避免“先取全书 Top N 再过滤本节”造成 Section recall 丢失；
- canonical source identity 规则不变；
- 不修改 `search_index_v0_36.jsonl` 来适配 QA。

## 7. `EvidenceBuilder`

`EvidenceBuilder` 将 Search 命中转换为可发送给模型的有限真实教材证据。

流程：

```text
SearchHit
→ canonical identity check
→ SourceResolver.resolve(...)
→ scope check
→ deduplicate
→ bounded projection
→ deterministic sort
→ E1, E2, ...
```

每条 EvidenceItem 建议包含：

```text
evidence_id
course_id
book_id
chapter_id
section_id
source_kind
source_id
object_type
type_zh
number
title_zh
title_en
content_zh
formula
printed_page
pdf_page
source_anchor
```

规则：

- `evidence_id` 为本轮临时 ID：`E1`、`E2`……；
- canonical identity 全部来自 Runtime / SourceResolver；
- `source_anchor` 可以为 `null`，不得补造；
- 不因模型需要而改写教材事实；
- 同一 `(source_kind, source_id)` 只保留一次；
- 同一证据可包含必要的中文正文与公式，但不发送完整 object 原始 JSON；
- 第一版最多向模型发送 8 条 evidence；
- EvidencePack 总文本必须有上限，超出时按确定性排序截断；
- 完整教材、整章原文、全量 search index 均不得发送给在线 Provider。

建议默认：

```text
MAX_EVIDENCE_ITEMS = 8
MAX_EVIDENCE_TEXT_CODEPOINTS = 12000
```

这些上限属于服务器配置/常量，不由浏览器控制。

## 8. 服务器 `EvidenceGate`

模型调用前必须经过服务器机械证据门。

最低要求：

1. 至少 1 条经 SourceResolver 成功解析的 evidence；
2. 至少 1 条 evidence 含可回答内容，而不是纯标题空壳；
3. 最高检索相关度不能只是当前 SearchRuntime 的 generic type-only 命中；
4. evidence 必须属于当前 course 主教材；
5. Section 模式下 evidence 必须满足相应 Section scope。

若 Section gate 不通过，自动全书 fallback。

若 book gate 仍不通过：

- **不得调用在线模型**；
- 返回 HTTP 200 正常产品状态；
- `insufficient_evidence = true`；
- 使用服务器稳定中文提示，不采用模型生成拒答。

稳定提示：

```text
根据当前教材中检索到的内容，暂时无法可靠回答这个问题。
```

Search/index/SourceResolver 整体不可用属于基础设施故障，不能伪装成“教材证据不足”。

## 9. `ModelProvider` 抽象

内部协议：

```python
class ModelProvider(Protocol):
    def answer(self, request: ModelRequest) -> ModelResponse: ...
```

`ModelRequest` 只能包含：

- 当前 question；
- 当前 Section 显示身份（如有）；
- 有限近期 dialogue context；
- 本轮 EvidencePack；
- 严格回答规则；
- 允许的 answer style 枚举。

Provider 不负责：

- 搜索；
- 选择 course/book；
- 创建来源；
- 生成页码；
- 生成 source ID；
- 判断 SourcePage URL；
- 读取本地教材文件。

## 10. OpenAI-compatible Provider

Phase 1F v1 必须实现一个 OpenAI-compatible Provider，避免把业务层绑死到单一供应商。

本机服务器配置：

```text
BOOK_QA_BASE_URL
BOOK_QA_API_KEY
BOOK_QA_MODEL
```

可选服务器默认项：

```text
BOOK_QA_TIMEOUT_SECONDS=60
```

规则：

- API Key 只能由 Python/FastAPI 读取；
- Vite/React bundle 不得包含这些值；
- `.env.example` 只提供空值模板；
- 真实 `.env` / secret 文件必须在 `.gitignore` 范围内；
- GitHub CI 不需要真实 Key；
- Drive 同步包/备份不应包含真实 Key；
- Provider 未配置时，只有 QA 功能不可用，阅读、搜索、四模式、SourcePage 继续正常工作。

未来 Ollama/local provider 通过相同 `ModelProvider` 接口增加，不修改 `QARuntime` 业务逻辑。

## 11. 模型输入规则与连续追问

Phase 1F 支持 session-only 连续追问，但每一轮都重新检索教材 evidence。

模型输入：

```text
current question
+
recent dialogue context
+
current-turn EvidencePack
```

明确禁止：

```text
previous assistant answer == textbook evidence
```

历史 assistant 文本只能帮助解析“它”“前面这个定义”“那为什么”之类指代。

建议历史窗口：

- 最多最近 6 条消息（3 轮 user/assistant）；
- 总文本最多 6000 Unicode code points；
- 超限时从最旧消息开始截断；
- EvidencePack 不计入 history 上限。

模型 System 规则必须至少包含：

```text
你是当前教材的问答助手。
你只能依据本轮 <evidence> 中提供的教材证据回答。
对话历史只用于理解当前问题，不是事实证据。
不得使用你自己的外部知识补充教材事实。
不得创建教材中没有的定义、定理、公式、证明、页码或来源。
引用只能选择服务器提供的 evidence_id。
若证据不足，必须设置 insufficient_evidence=true。
```

## 12. 自动回答风格

模型输出必须标明：

```text
brief | explain | compare | proof
```

语义目标：

- `brief`：定义、是什么、简短结论；
- `explain`：为什么、怎么理解、直观解释；
- `compare`：比较两个概念/条件；
- `proof`：证明、推导、逐步论证。

所有 style 都受同一教材证据约束。

特别是 `proof`：如果 EvidencePack 不能支撑完整证明链，模型必须返回 `insufficient_evidence=true`，不得用自身数学知识补足缺失步骤。

## 13. 模型结构化输出 Schema

Provider 的模型输出只允许：

```json
{
  "answer": "字符串或 null",
  "evidence_ids": ["E1", "E3"],
  "insufficient_evidence": false,
  "answer_style": "explain"
}
```

字段规则：

- `answer_style` 只能为 `brief / explain / compare / proof`；
- `insufficient_evidence=false` 时 `answer` 必须为非空字符串；
- `insufficient_evidence=false` 时至少需要 1 个合法 `evidence_id`；
- `insufficient_evidence=true` 时最终用户提示由服务器生成，模型的 answer 不作为确定性教材回答展示；
- 模型不得返回 `source_id`、页码、anchor、URL、course/book identity 作为可信来源字段。

OpenAI-compatible adapter 应尽可能请求 JSON/structured response；无论上游是否支持原生 schema，服务器都必须执行严格 JSON parse + schema validation。

非法 JSON 可最多做 **1 次有限重试**；仍失败则返回 provider invalid response，不无限重试。

## 14. 双重证据判定

最终可展示教材答案必须同时满足：

```text
server EvidenceGate == sufficient
AND
model insufficient_evidence == false
AND
CitationValidator == valid
```

任意一项失败：

- 不展示为确定性教材回答；
- 不降级为“模型常识回答”；
- 不静默删除所有坏引用后继续显示答案。

模型二次判定为不足时返回：

```text
HTTP 200
insufficient_evidence = true
answer = null
citations = []
message = "根据当前教材中检索到的内容，暂时无法可靠回答这个问题。"
```

## 15. `CitationValidator`

模型回答后，服务器对 `evidence_ids` 进行 fail-closed 校验。

规则：

- ID 不在本轮 EvidencePack → 响应无效；
- 重复 ID → 可稳定去重并保留首次出现顺序；
- `insufficient_evidence=false` 且 ID 列表为空 → 响应无效；
- answer 非空但所有引用均非法 → 响应无效；
- 最终 citation 信息只能由服务器从 EvidenceItem 投影；
- 最终 source 必须仍可由 SourceResolver 解析；
- 不允许模型给出的页码/anchor 覆盖服务器值。

最终 Citation DTO：

```text
evidence_id
source_kind
source_id
chapter_id
section_id
object_type
type_zh
number
title_zh
title_en
printed_page
pdf_page
source_anchor
```

`source_anchor=null` 时 UI 显示“教材锚点暂未提供”，不得伪造。

## 16. API contract

新增：

```text
POST /api/courses/{course_id}/qa
```

请求：

```json
{
  "question": "为什么巴拿赫空间要求完备？",
  "section_id": "ch01_s01",
  "history": [
    {"role": "user", "content": "巴拿赫空间是什么？"},
    {"role": "assistant", "content": "……"}
  ]
}
```

`section_id` 可为 `null`。

响应示意：

```json
{
  "course_id": "functional_analysis_course",
  "book_id": "stein_shakarchi_functional_analysis_2011",
  "question": "为什么巴拿赫空间要求完备？",
  "answer": "……",
  "answer_kind": "generated",
  "answer_style": "explain",
  "scope_requested": "section_then_book",
  "scope_used": "book",
  "insufficient_evidence": false,
  "message": null,
  "citations": [
    {
      "evidence_id": "E1",
      "source_kind": "object",
      "source_id": "def_banach_space",
      "chapter_id": "ch01",
      "section_id": "ch01_s01",
      "object_type": "definition",
      "type_zh": "定义",
      "number": null,
      "title_zh": "巴拿赫空间",
      "title_en": "Banach space",
      "printed_page": 12,
      "pdf_page": 31,
      "source_anchor": null
    }
  ]
}
```

注意：示意 DTO 中的教材字段只说明 contract，不代表该具体 object/页码一定存在；实现测试必须使用仓库真实 canonical identity，不能把示例值写成教材事实。

## 17. 稳定错误语义

建议：

- `400 invalid_qa_question`：空问题、超长问题、非法 history；
- `404 course_not_found`：course 不存在；
- `404 section_not_found`：请求 section 不存在或不属于当前 course；
- `503 qa_unavailable`：Search/index/SourceResolver trust path 不可用；
- `503 qa_provider_unconfigured`：本机 Provider 未配置；
- `503 qa_provider_unavailable`：上游 provider 超时/限流/不可达；
- `502 qa_provider_invalid_response`：非法 JSON、schema 不符、citation 校验失败。

`insufficient_evidence` 始终是 HTTP 200 产品结果，不是系统错误。

所有用户可见错误使用稳定中文 DTO，不泄漏 traceback、Key、base URL 或上游原始敏感错误体。

## 18. QA 页面与入口

路由：

```text
/courses/:courseId/qa
/courses/:courseId/qa?section=ch01_s01
```

Course 页提供：

```text
教材目录
教材搜索
教材问答
```

Section 页提供：

```text
[问本节内容]
```

从 Section 进入时顶部明确显示：

```text
当前范围：第 X 章 · 当前小节
优先本节，必要时扩展到全书
```

从 Course 进入时：

```text
当前范围：整本教材
```

若实际 fallback 到全书，回答卡显示：

```text
回答依据：本节 + 教材其他章节
```

若未 fallback：

```text
回答依据：当前小节
```

## 19. 回答卡

每轮回答至少包含：

- 用户问题；
- “AI 生成回答，依据下方教材来源”标签；
- 回答正文；
- answer style 对应的排版结构；
- `scope_used`；
- Citation cards；
- “查看教材来源”动作。

Citation 点击必须复用 Phase 1D/1E 现有 SourcePage；不增加 QA 专用来源页。

## 20. 当前会话连续问答状态

QA session 使用：

```text
sessionStorage
key = book:qa-session:${courseId}
```

建议状态：

```ts
interface QASessionState {
  route: string
  messages: QAMessage[]
  scrollY: number
  activeCitationSourceId: string | null
}
```

`QAMessage` 可保存：

- role；
- 用户问题或服务器验证后的回答文本；
- answer style；
- scope used；
- 已验证 citation identity。

明确不保存：

- API Key；
- Provider server config；
- EvidencePack 教材全文；
- 原始模型 prompt；
- 原始模型 response；
- SearchRuntime 全量命中；
- 教材完整正文。

sessionStorage 只用于当前浏览器会话 UI 恢复，不是长期权威记录；关闭 tab/session 后允许清除。

## 21. QA → Source → Return

点击 citation：

```text
QAPage
→ existing SourcePage
→ Return
→ same QA session
```

返回时恢复：

- 原 route / section context；
- 当前 QA messages；
- 回答；
- 已验证 citations；
- citation 展开/active 状态；
- 原滚动位置。

**返回时不重新调用在线模型。**

原因：

- 避免重复费用；
- 避免同一历史问题因 nondeterministic generation 改变措辞；
- 用户已经拿到的是服务器验证后的 session display state。

但该缓存回答仍只被视为“本次会话生成回答”，不是教材正文或长期学习事实。发送下一轮问题时必须重新检索本轮 evidence。

## 22. 隐私与安全边界

在线模型只收到：

```text
当前问题
+
有限最近对话
+
本轮有限 EvidencePack
```

不得发送：

- 完整教材；
- 全量索引；
- 本地绝对路径；
- repository metadata；
- GitHub/Drive credentials；
- API Key；
- browser storage 全量；
- StudyRecord；
- 未经本轮选中的教材对象。

密钥只在 server-side configuration。

## 23. 日志与可观测性

默认日志允许记录：

- course_id；
- section_id；
- scope_requested / scope_used；
- evidence_count；
- evidence gate result；
- provider adapter / model name；
- latency；
- stable error code。

默认不记录：

- API Key；
- 完整问题正文；
- 完整 history；
- 完整 EvidencePack；
- 完整 prompt；
- 完整 provider raw response；
- 完整生成回答。

## 24. Provider 失败处理

QA 故障不得拖垮 Book App 其他能力。

- Provider 未配置：QA 显示“教材问答尚未配置模型服务”；
- 上游超时/限流/502：保留用户输入，显示可重试错误；
- 非法 JSON：最多自动重试 1 次；
- citation invalid：fail closed；
- 证据不足：正常 200，不调用/不依赖模型拒答；
- 任何 QA 错误都不影响 Library、Course、Chapter、Section、Search、SourcePage。

## 25. Fake Provider 与 CI

CI 绝不能依赖真实收费 API 或 secret。

实现：

```text
DeterministicFakeModelProvider
```

用于：

- Runtime tests；
- App/API tests；
- React contract tests；
- Playwright acceptance。

Fake provider 必须支持稳定模拟：

- 正常结构化回答；
- `insufficient_evidence=true`；
- malformed JSON / invalid schema；
- timeout/unavailable；
- invalid evidence ID；
- duplicate evidence IDs；
- empty answer。

真实 OpenAI-compatible Provider 仅做本机人工 smoke test，不成为 GitHub CI gate。

## 26. Runtime 测试矩阵

至少覆盖：

1. Section 有足够证据 → 不扩大全书；
2. Section 不足 → 自动扩大全书；
3. 全书仍不足 → 不调用 provider；
4. Course 模式直接全书；
5. SearchRuntime 不可用；
6. SourceResolver 失败；
7. EvidenceBuilder 去重；
8. EvidencePack item/text 上限；
9. history 不作为 evidence；
10. history 窗口正确截断；
11. server EvidenceGate sufficient/insufficient；
12. model second-gate insufficient；
13. model valid citations；
14. model nonexistent evidence ID；
15. duplicate citations stable dedupe；
16. non-empty answer + empty citations invalid；
17. invalid JSON retry once then fail；
18. `brief/explain/compare/proof` schema validation；
19. real Functional Analysis canonical source identity preservation。

## 27. App/API 测试矩阵

覆盖：

- valid QA `200`；
- insufficient `200`；
- blank question `400`；
- invalid history `400`；
- unknown course `404`；
- unknown/wrong-course section `404`；
- runtime unavailable `503`；
- provider unconfigured `503`；
- provider unavailable `503`；
- provider invalid response `502`；
- Section → book scope DTO；
- citation canonical identity；
- server never exposes API Key/base_url secret values。

## 28. Web 测试矩阵

覆盖：

- Course 页全书 QA 入口；
- Section 页“问本节内容”；
- Section scope label；
- book scope label；
- 连续追问；
- `brief / explain / compare / proof` 展示；
- insufficient evidence；
- provider 未配置；
- provider 异常；
- citations；
- Source link；
- Source → QA 返回；
- sessionStorage 恢复；
- sessionStorage 不包含 EvidencePack/Key；
- 390×844 不发生 body 横向溢出。

## 29. Playwright 验收

CI 使用真实 Functional Analysis Runtime + Fake Provider。

主流程：

```text
Library
→ Functional Analysis
→ Chapter
→ Section
→ 问本节内容
→ 提交真实可命中问题
→ 显示教材回答
→ 显示真实 citation
→ 点击 SourcePage
→ 返回 QA
→ 原回答/引用/滚动恢复
→ 连续追问
```

额外流程：

1. Course 页全书问答；
2. Section 证据不足触发 book fallback；
3. 全书 insufficient；
4. 390×844 QA → Source → QA round trip。

所有 acceptance query 必须使用仓库真实教材可验证内容，不在测试中虚构 canonical source identity。

## 30. CI gate

Runtime workflow：

- Python 3.11 / 3.12 / 3.13；
- QA unit tests；
- Functional Analysis real-data fake-provider smoke；
- 既有 Runtime reference tests 全部继续通过。

Book App UI workflow：

- App/API QA tests；
- Web Vitest；
- TypeScript typecheck；
- Vite/PWA build；
- Chromium Playwright QA acceptance；
- 既有 Phase 1D/1E acceptance 不回归。

## 31. 数据完整性约束

Phase 1F 不得为了“让 QA 能答”而修改 canonical textbook facts。

不得静默改写：

- `books/functional-analysis/search_index_v0_36.jsonl`；
- PageMap；
- chunk/structure 文件；
- canonical object IDs；
- source anchors；
- 中英教材内容投影。

若实现过程中发现真实 source-data defect，应作为单独可审计的数据修复处理，不得藏在 prompt 或 QA adapter 内补偿。

## 32. Phase 1F 完成标准

只有以下全部满足，Phase 1F 才可在 `ROADMAP.md` 标为 COMPLETE：

- [ ] `QARuntime` 建立教材证据与生成模型 trust boundary；
- [ ] `EvidenceBuilder`；
- [ ] server `EvidenceGate`；
- [ ] Section 优先 → book fallback；
- [ ] Course 直接 book scope；
- [ ] 严格“仅当前教材回答”；
- [ ] `ModelProvider` 抽象；
- [ ] OpenAI-compatible Provider；
- [ ] server-side `BOOK_QA_BASE_URL / API_KEY / MODEL` 配置；
- [ ] `.env.example` 且真实 secret 不进入 GitHub/Drive；
- [ ] 模型结构化 JSON schema；
- [ ] 模型 `insufficient_evidence` 二次证据门；
- [ ] `CitationValidator` fail closed；
- [ ] provider 只能引用服务器 evidence ID；
- [ ] Course QA 入口；
- [ ] Section QA 入口；
- [ ] session-only 连续追问；
- [ ] 每轮 fresh retrieval，历史回答永远不是 evidence；
- [ ] 自动 `brief/explain/compare/proof`；
- [ ] QA → Source → QA 不重新调用模型并恢复状态；
- [ ] 生成回答不写回教材；
- [ ] EvidencePack/Key 不进入浏览器 sessionStorage；
- [ ] Python / API / Web / Playwright tests；
- [ ] 390×844 验收；
- [ ] CI 不依赖真实 API Key；
- [ ] 既有 Phase 1D / 1E 功能与测试不回归；
- [ ] README / 本机配置说明 / ROADMAP 在实现完成后更新。

## 33. 与现有预实现分支的关系

仓库当前已存在 `feature/textbook-qa-phase-1f`，其 head 在本设计产生前已经包含 Phase 1F 代码与旧版 spec/plan。

在本设计获得用户确认前：

- 该 feature 分支不作为本设计的权威实现基线；
- 不因该分支已有代码而反向修改本设计决策；
- 不直接把该分支合入 `main`；
- 用户批准本 spec 后，应先对 feature 分支做 gap audit；
- 能复用且符合本 spec 的代码可保留；
- 与本 spec 冲突的实现必须修改或重写；
- 通过完整 completion gate 后再进入 PR/merge 流程。

## 34. 下一步

本 spec 经用户确认后：

1. 进入 implementation-plan 阶段；
2. 以本 spec 为唯一 Phase 1F 设计依据，对现有 `feature/textbook-qa-phase-1f` 做差距审计；
3. 输出具体 implementation plan；
4. 再开始/修正功能代码；
5. 完整测试通过后提交 PR。
