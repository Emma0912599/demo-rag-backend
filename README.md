# demo-rag-backend

一个最小可用的 RAG 后端样例，基于 FastAPI，内置流式对话接口、RAG 组装流程（Query Rewrite → Search → Answer）、可插拔缓存（Redis/本地字典），以及统一的事件式流响应格式（JSON Lines over text/event-stream）。

## 特性

- FastAPI + Uvicorn，内置 OpenAPI 文档（/docs）
- 统一的消息/事件 Schema（Pydantic v2）
- `/v1/chat/completions`：支持非 RAG 与 RAG 两种模式的流式对话
- `/v1/chat/halt`：中止会话，降低后端压力
- `/v1/chat/summarize`：对一段对话生成标题（占位实现）
- 缓存：默认尝试 Redis；失败时回退到本地内存

## 运行环境

- Python 3.10+
- 建议安装 uv（可选）：更快的 Python 包与运行管理

## 安装

使用 uv（推荐）：

```bash
make install
```

或使用 pip：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 配置

默认从项目根目录的 `config.yaml` 读取配置；其中：

- OpenAI 兼容接口（节名 `openai`）：
	- `api_url`: 基础地址（如自建 OpenAI 兼容服务）
	- `api_key`: 密钥
	- `model_name`: 模型名
- Redis（节名 `redis`）：`host`/`port`/`db`/`password`/`encoding`

环境变量可覆盖 OpenAI 相关配置（优先级最高）：

- `OPENAI_API_KEY`
- `OPENAI_API_BASE`
- `OPENAI_MODEL`

示例（见 `config.yaml`）：

```yaml
openai:
	api_url: your_api_url
	api_key: secret
	model_name: QwQ-32B

redis:
	host: localhost
	port: 6379
	db: 0
	password: my_password
	encoding: utf-8
```

注意：启动时会优先尝试创建 Redis 连接；若失败，将回退为本地内存缓存（不跨进程、不持久）。

## 运行

开发模式（带热重载）：

```bash
make run
```

启动后访问：http://127.0.0.1:8000/docs 查看交互式文档。

## 快速上手（cURL 示例）

1) 非 RAG 对话（流式）：

```bash
curl -N -H "Content-Type: application/json" \
	-X POST http://127.0.0.1:8000/v1/chat/completions \
	-d '{
		"rag_enable": false,
		"chat_id": "chat-1",
		"message_id": "msg-1",
		"query": [
			{"role": "user", "content": "讲讲Transformer是什么？"}
		]
	}'
```

服务端会以 `text/event-stream` 输出按行分隔的 JSON，每行一个完整事件对象：Init → Answer(多段) → End。

2) RAG 对话（流式）：

```bash
curl -N -H "Content-Type: application/json" \
	-X POST http://127.0.0.1:8000/v1/chat/completions \
	-d '{
		"rag_enable": true,
		"chat_id": "chat-2",
		"message_id": "msg-1",
		"query": [
			{"role": "user", "content": "什么是注意力机制？"}
		]
	}'
```

事件顺序：Init → Query Rewrite(多段) → Search(一次，包含检索结果) → Answer(多段) → End。

3) 终止会话：

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/halt?chat_id=chat-2"
```

4) 生成对话标题：

```bash
curl -H "Content-Type: application/json" \
	-X POST http://127.0.0.1:8000/v1/chat/summarize \
	-d '[{"role": "user", "content": "请帮我总结这段对话的主题"}]'
```

## API 概览

- `POST /v1/chat/completions` 流式对话（RAG/非 RAG）
- `POST /v1/chat/halt` 终止会话（query 参数：`chat_id`）
- `POST /v1/chat/summarize` 生成标题（请求体：Message 列表）

详见 `docs/api.md`。

## 开发脚本

```bash
make lint      # 代码规范（ruff）
make format    # 代码格式（black）
make test      # 运行测试（如有 tests）
make precommit # 运行 pre-commit 钩子
```

## 目录结构

- `src/main.py` 应用入口，注册路由与缓存生命周期
- `src/core/` 业务核心（API、聊天、提示词、DTO 等）
- `src/schema.py` 统一数据与事件 Schema
- `src/llm.py` OpenAI 兼容 LLM 客户端（支持流）
- `src/cache.py` 缓存抽象、本地缓存与 Redis 实现
- `config.yaml` 配置文件
- `docs/api.md` API 详细说明
