"""API 路由"""
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse

from src.cache import Cache
from src.llm import LLMClient
from src.response import ApiResponse
from src.schema import Message
from src.core.user import UserProfile, save_user_profile

from .chat import ChatService, RAGService
from .dto import ChatRequest

router = APIRouter()
logger = logging.getLogger(__name__)


def get_qwq_client() -> LLMClient:
    return LLMClient()


def get_cache(request: Request) -> Cache:
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        raise RuntimeError("Cache is not configured on app.state.cache")
    return cache


# Avoid calling Depends(...) inside default args (ruff B008)
CACHE_DEP = Depends(get_cache)
QWQ_LLM_DEP = Depends(get_qwq_client)


@router.get("/")
async def index():
    return RedirectResponse(url="/docs")


@router.post("/users", response_model=dict)
async def create_user(user_profile: UserProfile):
    """
    接收前端发送的用户信息，验证后存入数据库
    """
    try:
        user_id = save_user_profile(user_profile)
        return {"status": "success", "user_id": str(user_id)}
    except Exception as e:
        logger.error(f"Error saving user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    cache: Cache = CACHE_DEP,
    llm_client: LLMClient = QWQ_LLM_DEP,
):
    """
    对话补全接口，分为 RAG 启用/关闭两类

    流式响应的内容格式是 `text/event-stream`;
    响应保证：单次请求中每条 JSON 结构是完整的.
    """

    if request.rag_enable:
        chat_service = RAGService(cache=cache, llm_client=llm_client)
    else:
        chat_service = ChatService(cache=cache, llm_client=llm_client)

    async def stream_generator():
        async for chunk in chat_service.generate(
            chat_id=request.chat_id,
            message_id=request.message_id,
            messages=request.query,
        ):
            yield chunk

    try:
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        return ApiResponse.fail(msg=str(e))


@router.post("/v1/chat/halt")
async def chat_halt(chat_id: str, cache: Cache = CACHE_DEP):
    """
    会话终止接口，截断RAG的回答链路，以减小服务器端压力

    客户端接收到 /completions 里的 end 事件后，终止当前会话请求.
    """
    service = ChatService(cache=cache)
    await service.halt_chat(chat_id)
    return ApiResponse.success(data={"chat_id": chat_id, "status": "halted"})


@router.post("/v1/chat/summarize")
async def chat_summarize(messages: list[Message], cache: Cache = CACHE_DEP):
    """会话标题生成接口，为一段会话总结标题"""
    service = ChatService(cache=cache)

    query = messages[-1].content
    title = await service.generate_chat_title(query)

    return ApiResponse.success(data={"title": title})
