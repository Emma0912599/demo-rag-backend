"""封装大模型相关接口"""

import os
from collections.abc import AsyncGenerator

import openai
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from src.config import BaseConfig
from src.schema import Message


class OpenAIConfig(BaseConfig):
    """
    OpenAI 兼容接口的配置项.
    """

    api_key: str
    api_url: str
    model_name: str

    def __init__(self, **data):
        """支持两种初始化方式：

        1) 直接传入 api_key/api_url/model_name；
        2) 无参数时自动从 config.yaml 与环境变量加载。

        环境变量优先级最高：OPENAI_API_KEY、OPENAI_API_BASE、OPENAI_MODEL。
        """
        if not data:
            # 读取字典配置用于与环境变量合并
            data = self.from_yaml_dict()

        api_key = os.getenv("OPENAI_API_KEY", data.get("api_key"))
        api_url = os.getenv("OPENAI_API_BASE", data.get("api_url"))
        model_name = os.getenv("OPENAI_MODEL", data.get("model_name"))

        super().__init__(api_key=api_key, api_url=api_url, model_name=model_name)

    @classmethod
    def from_yaml(cls, path: str | None = None) -> "OpenAIConfig":
        """从 YAML 加载并返回 OpenAIConfig 实例。"""
        return super().from_yaml(path)  # type: ignore[return-value]

    @classmethod
    def from_yaml_dict(cls, path: str | None = None) -> dict:
        return super().from_yaml_dict(path)


class LLMGenerationConfig(BaseModel):
    """LLM 生成参数配置"""

    model: str
    stream: bool = Field(default=False)

    # specific hyperparameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度，控制随机性")
    max_tokens: int | None = Field(default=None, ge=1, description="最大生成token数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop: list | None = Field(default=None, description="停止生成的标记")

    model_config = ConfigDict(extra="forbid")


class LLMClient:
    """
    负责管理与 LLM API 的连接与生成，只考虑 OpenAI 接口的提供方.
    """

    def __init__(self, config=None):
        if config is None:
            config = OpenAIConfig()
        self.openai_config = config
        self.client = openai.AsyncOpenAI(
            api_key=self.openai_config.api_key,
            base_url=f"{self.openai_config.api_url}",
            timeout=60,
        )
        self.default_config = LLMGenerationConfig(
            model=self.openai_config.model_name,
        )

    async def generate(self, messages: list[Message]) -> str:
        openai_messages = self._convert_messages(messages)
        config = self.default_config.model_copy(update={"stream": False})

        try:
            call_params = config.model_dump(exclude_none=True)

            response = await self.client.chat.completions.create(
                messages=openai_messages, **call_params
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"调用 OpenAI API 时发生错误: {e}")
            raise

    async def generate_stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        query = self._convert_messages(messages)
        config = self.default_config.model_copy(update={"stream": True})
        stream = None

        try:
            call_params = config.model_dump(exclude_none=True)
            stream = await self.client.chat.completions.create(messages=query, **call_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        finally:
            try:
                if stream is not None:
                    await stream.close()
            except Exception:
                pass

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """统一消息格式，去除 Attachment"""
        return [{"role": message.role, "content": message.content} for message in messages]

    def _generate_message(self, prompt: str, system_prompt: str = None) -> Message:
        return Message(
            role="user",
            content=f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
        )
