# Book r6 → mygpt：只读选段授权桥（评审候选）

日期：2026-09-23。当前能力是 **真实 r6 归档数据 → Book 选段授权 → mygpt 接收端 → 本机 HTTP / Pydantic AI TestModel**，不是手机 APK 已接通，也不是正式 AI 教师。默认不启动、不读取私人笔记或作答、不写 StudyRecord、不调用真实/付费模型。

## 1. 两个代码库的职责

Book 保有教材、Reader、选段投影和授权状态；mygpt 保有接收端、决策和固定 SDK 联调回复。Book 通过同进程受信任对象向接收端注入 `AuthorityPort`；HTTP 调用者不能替换数据源、模型或解析器。不会把 Book 语料复制到 mygpt。

Book 候选目录：`integrations/mygpt_selection/`，基于 r6 checkpoint `7283f2eef7610d67c6b92b2ef7c513e1225ad957`。旧 `app/` Web 树不等同于 r6 Reader，不得整树覆盖它。mygpt 配套接收端：`brain/mygpt_brain/book_bridge.py`，实现提交 `fa9f17a0eb4fb015d76b419865f1b49a2d325f0e`，分支 `feat/book-live-selection-v1-20260923`。

## 2. 真实源码身份

原有 Drive 文件：`Book-App-Source-CURRENT-r6-20260922.zip`，ID `1UiVow02Huh3r8qKBH8v4bL3D9OfkQ8_R`，70,090,018 bytes，SHA-256 `19315e8aeebe2db5cf2f4b55e0a38f550967966af106491dfef67212b430adc1`。

解压目录中的 `CURRENT_SOURCE_MANIFEST.json` 必须匹配 SHA-256 `15d9a1838023e8cf1d05835ddff80da28dde8cc2feaf01e1dbd3f718dff8c388`。启动时核验 112 个 Reader / JSON 成员；每次读取课程 JSON 再验哈希，图片按需验哈希。源变化时拒绝并要求重新确认，不接受同版本号下的静默替换。这不证明用户手机已安装 APK 的身份。

## 3. 使用流程与层级

独立宿主打开原 Reader 页面时，只在内存中按固定锚点加入可选选段控件。原文件、连续密集正文和正常 Book 应用不被改写。点击“开启本次只读连接”后，选择一段、核对预览和层级，再点击“确认只读交给 mygpt”；最后明确点击“测试解释这段”，才调用本地 TestModel。仅阅读、打开控件和选择草稿不会解释。

四种层级、五种内容路径：

- `source`：原始转录正文，不自动替换成校正或补录。
- `completion`：原页补录正文；必须符合补录来源标记。
- `correction`：与原始标题、正文和检查身份绑定的高置信 AI 校正；仍不是官方勘误。
- `derived`：分别选择 `hint` 或 `solution`；仍不是教材原文或官方答案。

每一种都显式选择 `raw` 或 `display`。前者保留原始文字 / LaTeX，后者使用 Reader 的 `render_text` / `render_latex`。合法公式编号中的撇号保留；习题可以引用其他已知小节。图片不进入选段正文，仅保留“非文字部分已排除”的告知；正文超过 12,000 字符或 64,000 字节则拒绝。空正文不能被假造为成功选段。

## 4. 授权与取消语义

会话默认 900 秒，选段默认 90 秒；授权、HMAC 密钥、选段和收据只存在当前进程内存。会话 Cookie 使用 HttpOnly / SameSite=Strict。授权票据绑定课程、书籍、版本、小节、record、layer、portion、表示方式、内容哈希、session、epoch 和时效。

新选段先占用递增序号并让旧选段失效，然后读取源文件；慢的旧请求不能在新选择或清除之后复活。重复请求不会续期或再次执行模型。同请求 ID 不同内容返回冲突。接收端在首次消费、重复回复和最后提交时都重新验证当前授权与源内容。

取消请求提前到达时也建立取消记录；取消或撤销后，未完成结果不能成为完成收据。已实际交付的字节不能被撤回。切段、翻页、切模式、离开、隐藏与过期的浏览器失效逻辑已经实现，但本轮浏览器策略阻止了实测，不能宣称这些 UI 路径已通过。

## 5. 安全范围

仅绑定 `127.0.0.1`，支持随机端口。写 API 要求精确同源 Origin、Host、固定客户端头与 JSON；拒绝 CORS、重复关键头、Transfer-Encoding 和超限请求体。固定静态文件和 API allowlist；不提供任意文件下载或 Book 笔记导出。最多 16 个并行请求，默认 16 个会话、每会话 64 个命令收据、接收端 128 个请求收据；达到容量要求重连或重启，不静默驱逐防重放记录。

这是受信任本机开发环境，不是 TLS、多用户、Android IPC 或对本机恶意进程的隔离。浏览器“明确点击”是产品交互要求，不是防范本机恶意进程伪造 HTTP 的证明。原 Reader 的字号等非敏感显示设置仍由 Reader 自己处理；宿主禁用笔记、作答、自评、进度写入，状态读取返回明确的空只读状态而非用户真实状态。

## 6. 运行与复现（Linux / Python 3.13）

需要：两个评审分支的源码；原有 r6 ZIP 的单独解压目录；Node 22；mygpt 现有 39-wheel hash lock 安装的独立 Python 3.13 环境。该依赖锁不是跨平台通用锁，Windows / Android 未验收。不要在含有不同 Starlette/FastAPI 版本的系统 Python 环境中混装。

```bash
# 按实际位置设置；R6_ROOT 是包含 CURRENT_SOURCE_MANIFEST.json 的目录。
export BOOK_CHECKOUT=/path/to/Book
export MYGPT_CHECKOUT=/path/to/mygpt
export R6_ROOT=/path/to/verified-r6
export PY=/path/to/locked-venv/bin/python
export PYTHONPATH="$BOOK_CHECKOUT/integrations/mygpt_selection:$MYGPT_CHECKOUT/brain"

"$PY" -m book_mygpt_selection.host --r6-root "$R6_ROOT" --port 0
# 终端仅打印本机 URL 与非敏感身份；Ctrl+C 停止。
```

选段投影和授权的纯单元测试不需要整个 r6 或 mygpt：

```bash
cd "$BOOK_CHECKOUT"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$PY" -m pytest \
  -c /dev/null --confcutdir=integrations/mygpt_selection \
  integrations/mygpt_selection/tests -q
node --test integrations/mygpt_selection/tests/projection.test.cjs
node --check integrations/mygpt_selection/book_mygpt_selection/web/bridge.js
```

实际归档联调需要配套 SDK 与两个源码路径：

```bash
"$PY" integrations/mygpt_selection/scripts/check_conformance.py \
  --r6-root "$R6_ROOT" --output /new/path/conformance.json
"$PY" integrations/mygpt_selection/scripts/accept_http.py \
  --r6-root "$R6_ROOT" --output /new/path/http-acceptance.json
```

每轮使用新的证据路径，勿覆盖历史验收。报告保留选段身份、计数与哈希，不保存教材正文、Cookie、私人笔记或作答。JavaScript 全量向量文件可重建，正式归档只保留摘要及其哈希。

## 7. 本轮已验证与未验证

| 项目 | 结果及范围 |
|---|---|
| Book Python | 68 项通过；合成输入投影与授权，不是整个旧 Book 仓库回归 |
| Book JavaScript | 18 项通过；Node 投影单元测试，不是浏览器 |
| 真实 r6 一致性 | 95 小节，19,174 个向量，0 差异；17,330 个正文成功、1,844 个预期空正文拒绝 |
| 真实 HTTP + SDK | 56 项通过，5 种真实 Book 内容路径，5 次实际 TestModel 调用，付费调用 0 |
| mygpt SDK | 本地 352 项通过；远端 run 35826642389 的两个新环境各 352 通过、0 跳过、0 失败 |
| UI 浏览器 | 未通过验收；本机托管浏览器在导航时返回 ERR_BLOCKED_BY_ADMINISTRATOR，未修改策略或绕过 |
| Android / 真实模型 | 未执行；无新 APK、未验证手机源身份、未验收教学质量 |

上述 19,174 是表示与身份一致性，不是 19,174 道题正确性，也不是内容全书校读完成。独立审阅仍未完成。

## 8. 唯一下一步

在允许 localhost 的受信任浏览器执行环境中，对本候选的精确代码做完整浏览器验收：真实选段、层级切换、两阶段确认、导航/隐藏/过期失效、取消与迟到回复、授权/撤销竞态、移动布局、字号和 LaTeX、不访问外网、不写学习记录。保存初次失败和最终证据，完成独立审阅后再讨论 Android 同机桥；不自动启用真实模型，不自动合并 PR，不解决已有 mygpt PR #5/#6 冲突。
