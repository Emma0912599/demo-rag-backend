# API 文档

本文档描述 demo-rag-backend 已实现的接口与数据结构。所有接口均挂载在根路径（无全局 prefix），默认返回 JSON；流式接口采用 `text/event-stream`，每行一个完整 JSON 对象（JSONL）。

## 通用数据结构（节选）

- Message
	- role: "user" | "assistant"
	- content: string
	- attachment: Attachment | null
- 事件类型 ResponseEventType: "Init" | "Query Rewrite" | "Search" | "Answer" | "End"
- ChatStatus: ACTIVE=1, COMPLETED=0, TERMINATED=-1

事件消息统一结构：

```json
{"event": "...", "data": {}}
```

流式输出时，每行一个独立 JSON（末尾换行），建议按行解析。

## GET /

重定向到内置文档 `/docs`。

## POST /v1/chat/completions

说明：

- 流式聊天接口。根据 `rag_enable` 为 false/true，分别走非 RAG 与 RAG 工作流。
- 响应头：`Content-Type: text/event-stream`
- 事件顺序：
	- 非 RAG：Init → Answer(多段) → End
	- RAG：Init → Query Rewrite(多段) → Search(一次) → Answer(多段) → End

请求体（application/json）：

```json
{
	"rag_enable": true,
	"chat_id": "chat-123",
	"message_id": "msg-1",
	"query": [
		{"role": "user", "content": "什么是注意力机制？"}
	]
}
```

字段说明：

- rag_enable: 是否启用 RAG 流程
- chat_id: 会话 ID，用于状态追踪与中止
- message_id: 本轮消息 ID
- query: 消息数组（至少 1 条），仅使用 `role` 与 `content`

示例响应（RAG 开启，按行示意）：

```json
{"event":"Init","data":{"chat_id":"chat-123","message_id":"msg-1","created_at":1724660000.0}}
{"event":"Query Rewrite","data":{"content":"重写后的问题..."}}
{"event":"Query Rewrite","data":{"content":"（后续流片段）"}}
{"event":"Search","data":{"doc":[{"idx":0,"title":"...","authors":[{"name":"...","institution":"..."}],"publicationDate":"...","language":"...","keywords":["..."],"publisher":"...","journal":"..."}],"chunks":[{"id":1,"doc_id":0,"text":"...","source":[{"type":"document","id":1,"url":"..."}]}]}}
{"event":"Answer","data":{"content":"答案片段1"}}
{"event":"Answer","data":{"content":"答案片段2"}}
{"event":"End","data":{"completion_time":1724660005.1,"end_reason":0}}
```

错误与中止：

- 服务器内部异常会记录日志，并在内部将会话状态标记为 TERMINATED，然后结束流；客户端应以 End 事件为准完成解析。
- 若客户端调用 `/v1/chat/halt` 将状态置为 TERMINATED，服务端会在下一次状态检查后终止后续流输出。

## POST /v1/chat/halt

说明：终止指定 chat_id 的会话，尽快停止流式生成，缓解资源开销。

请求：Query 参数

- chat_id: string（必填）

响应（application/json）：

```json
{
	"code": "200",
	"msg": "请求成功",
	"data": {"chat_id": "chat-123", "status": "halted"}
}
```

可能错误：

- 缺少 chat_id 时返回 400 样式的错误封装。

## POST /v1/chat/summarize

说明：根据传入的一段对话（Message 列表）生成一个简短标题。目前为占位实现：直接截取最后一条用户输入的前 10 个字符。

请求体（application/json）：

```json
[
	{"role": "user", "content": "请总结以上对话主题"},
	{"role": "assistant", "content": "..."}
]
```

响应：

```json
{
	"code": "200",
	"msg": "请求成功",
	"data": {"title": "请总结以..."}
}
```

## 状态机与事件

- Init：服务端分配/确认 chat_id、message_id，并标记状态 ACTIVE
- Query Rewrite：仅在 RAG 模式，基于提示词重写用户问题（流式）
- Search：仅在 RAG 模式，返回一次检索上下文（当前使用内置示例 JSON mock）
- Answer：模型回答（流式）。服务端每次片段输出前都会检查会话状态：
	- ACTIVE：继续输出
	- 非 ACTIVE（COMPLETED/TERMINATED）：停止输出
- End：流结束事件，`end_reason`：0=正常完成；-1=提前终止

## 兼容性与注意事项

- LLM 客户端使用 OpenAI 兼容接口（openai-python >= 1.30，Async 客户端），请正确配置 `api_url`、`api_key`、`model_name`。
- 当 Redis 不可用时，会自动回退到本地内存缓存（仅当前进程有效）。
- Search 阶段目前使用 `core/example_search_result.json` 作为示例数据；接入真实文档服务时替换 `RAGService.search_relevant_docs()` 实现即可。
