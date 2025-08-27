"""通用 API 响应"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    通用 API 响应模型
    """

    code: str = Field(..., description="响应状态码")
    msg: str = Field(..., description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: T | None = None, msg: str = "请求成功") -> "ApiResponse[T]":
        return cls(code="200", msg=msg, data=data)

    @classmethod
    def fail(cls, msg: str = "请求失败", code: str = "400") -> "ApiResponse[T]":
        return cls(code=code, msg=msg, data=None)

    model_config = ConfigDict(
        json_schema_extra={"example": {"code": "200", "msg": "请求成功", "data": {}}}
    )
