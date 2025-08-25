"""接口请求的数据模型"""

from pydantic import BaseModel, Field, field_validator

from src.schema import Message


class ChatRequest(BaseModel):
    """会话请求"""

    rag_enable: bool
    chat_id: str
    message_id: str
    query: list[Message] = Field(..., min_length=1)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: list[Message]) -> list[Message]:
        if not v:
            raise ValueError("query must not be empty")
        return v
