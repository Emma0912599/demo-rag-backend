"""配置类工具"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, List

import yaml
from pydantic import BaseModel, AnyHttpUrl

try:
    from loguru import logger
except ImportError:
    logger = None


class BaseConfig(BaseModel):
    """通用配置基类。

    提供从 YAML 文件加载当前配置类字段的能力：

    - 默认从项目根目录 `config.yaml` 读取；
    - 自动根据类名推断配置节名（去掉尾缀 "Config"，并小写，如 `OpenAIConfig` -> `openai`）；
    - 也支持顶层直接平铺字段（无节名时），仅提取当前模型字段；
    - 找不到文件时返回空字典，便于上层用环境变量等覆盖；
    - YAML 解析错误将抛出异常。
    """

    yaml_section: ClassVar[str | None] = None

    @classmethod
    def _default_config_path(cls) -> Path:
        return Path(__file__).resolve().parents[1] / "config.yaml"

    @classmethod
    def _infer_section_name(cls) -> str:
        if cls.yaml_section:
            return cls.yaml_section
        name = cls.__name__
        name_lower = name.lower()
        if name_lower.endswith("config"):
            name_lower = name_lower[: -len("config")]
        return name_lower

    @classmethod
    def _filter_model_fields(cls, data: Mapping[str, Any] | None) -> dict:
        if not isinstance(data, Mapping):
            return {}
        allowed = set(getattr(cls, "model_fields", {}).keys())

        if not allowed:
            return dict(data)

        return {k: v for k, v in data.items() if k in allowed}

    @classmethod
    def from_yaml_dict(cls, path: str | None = None) -> dict:
        cfg_path = Path(path) if path else cls._default_config_path()

        try:
            with open(cfg_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except FileNotFoundError:
            if logger:
                logger.debug(f"配置文件未找到: {cfg_path}. 将返回空配置以便使用环境变量/默认值。")
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件 YAML 解析失败: {e}") from e

        section = cls._infer_section_name()
        section_data = raw.get(section)

        if isinstance(section_data, Mapping):
            return cls._filter_model_fields(section_data)

        return cls._filter_model_fields(raw)

    @classmethod
    def from_yaml(cls, path: str | None = None) -> "BaseConfig":
        data = cls.from_yaml_dict(path)
        return cls(**data)


class AppConfig(BaseConfig):
    """应用配置"""
    name: str = "FastAPI App"
    version: str = "0.1.0"
    root_path: str = ""
    yaml_section: ClassVar[str] = "app"

class CORSConfig(BaseConfig):
    """CORS 配置"""
    origins: List[AnyHttpUrl] = []
    methods: List[str] = ["*"]
    headers: List[str] = ["*"]
    yaml_section: ClassVar[str] = "cors"

class LoggingConfig(BaseConfig):
    """日志配置"""
    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "7 days"
    yaml_section: ClassVar[str] = "logging"

def init_logging():
    """初始化日志记录器"""
    if logger:
        log_config = LoggingConfig.from_yaml()
        logger.add(
            "logs/app.log",
            level=log_config.level.upper(),
            rotation=log_config.rotation,
            retention=log_config.retention,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

# 创建全局配置实例
app_config = AppConfig.from_yaml()
cors_config = CORSConfig.from_yaml()
