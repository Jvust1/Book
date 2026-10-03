# Live 本地学习聊天增量

基线是电脑已有 `Live_2870261303_Spine38_Windows_x64_preview/resources/app`，不是另造角色项目。原始发布清单写的是 `LOCAL_UNVERIFIED`；不能冒称 GitHub 提交 `4baf39bf...` 的构建。`provenance.json` 记录原始 37 个文件的 SHA-256。原程序和角色文件均不修改。

## 启动

使用 Windows PowerShell 执行本目录 `Start-Live-Study.ps1 -Port 8767`。启动器先核验原源码哈希，把已有 Electron 运行时和改动后的 app 放进工作区的独立副本，再启动副本。`-PrepareOnly` 只准备，不开窗口。

与 mygpt 共用环境变量 `LIVE_STUDY_TOKEN`；不要把凭据写进代码、聊天或日志。未提供时启动器会创建仅当前 Windows 用户可读的本地 token 文件，位于运行副本的 `study-private/live-token.txt`。该目录和用户配置均不在源码交付目录中。可传 `-RuntimeSource` 指定同一原版目录，`-RuntimeDirectory` 必须在工作区内。

默认只提供文字气泡和同会话回复；不会主动生成话语，不接模型，不录音，不调用 TTS。选中已有 Spine 角色时复用原有动画；没有角色时文字显示在现有 Live 控制台，不假装加载了 Live2D 模型。

## HTTP 合同（仅主进程）

所有请求需 `Authorization: Bearer <LIVE_STUDY_TOKEN>`，仅绑定 `127.0.0.1`，拒绝跨 Origin、错误 Host、重复关键头和大于 32 KiB 的请求。渲染进程仍禁止网络，CSP、sandbox、contextIsolation、nodeIntegration、webSecurity 保持原设置。

- `GET /study/health`：返回 `generation` 和 `renderer_mode`，不得当成 dot/model 已连接。
- `POST /study/present`：原 `mygpt.live2d-presentation.v1` 字段，加 `expires_at`（最长剩余 15 秒）和 `generation`。只有 generation 仍相等、可信 renderer 主 frame 确认 DOM 文字显示后，才返回 `status=presented, display_ack=true, message_id, session_id, renderer_mode`。重复 message id 不会重显，也不返回新的成功 ACK。
- `POST /study/invalidate`，正文 `{}`：原子递增 generation，取消待展示请求、清文字和回复队列，返回新 generation。旧 HTTP 请求即使晚到，也不能跨此代际显示。
- `POST /study/replies/take`，正文 `{ "session_id": "..." }`：只取该会话的一条 `mygpt.live-user-reply.v1`（request_id、session_id、reply_to_message_id、text、captured_at）。回复不得直接执行模型，仍须 mygpt 验证当前 Book 状态及会话。

mygpt 必须在 presentation 生命周期开始捕获本地失效序号；读取 health 后如果该序号变化则放弃。随后发送捕获的服务端 generation，不能给旧消息刷新 generation。HTTP 超时结果未知，不自动重试。ACK 后仍需再检查 Book 租约。隐藏测试 renderer 的 `renderer_mode=offscreen_test` 必须由生产适配器拒绝；测试只有显式授权才接受。

## 已观察与未完成

真实 Electron 44.4.4 隐藏窗口已验证：DOM 文字而非 HTML 执行、可信 sender 两帧 ACK、真实表单输入同会话取回一次、过期/停用撤销、伪 ACK 拒绝、旧请求跨撤销代际拒绝。测试画面明确标注“本地隐藏窗口测试”；这不是用户已看到角色、语音或模型生成内容的证明。

原角色资源加载与模型调用不在本次自动测试中；模型按用户要求暂不接入。不开公网端口，不改变原应用权限，不自动导入私有角色资源。

