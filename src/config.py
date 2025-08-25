"""配置类工具"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel

try:
    from loguru import logger  # type: ignore
except Exception:  # pragma: no cover
    logger = None  # type: ignore


class BaseConfig(BaseModel):
    """通用配置基类。

    提供从 YAML 文件加载当前配置类字段的能力：

    - 默认从项目根目录 `config.yaml` 读取；
    - 自动根据类名推断配置节名（去掉尾缀 "Config"，并小写，如 `OpenAIConfig` -> `openai`）；
    - 也支持顶层直接平铺字段（无节名时），仅提取当前模型字段；
    - 找不到文件时返回空字典，便于上层用环境变量等覆盖；
    - YAML 解析错误将抛出异常。
    """

    # subclass can override this attribute to specify the YAML section name
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
        allowed = set(getattr(cls, "model_fields", {}).keys())  # pydantic v2

        if not allowed:
            return dict(data)

        return {k: v for k, v in data.items() if k in allowed}

    @classmethod
    def from_yaml_dict(cls, path: str | None = None) -> dict:
        """从 YAML 文件加载并提取仅与当前模型字段匹配的字典。

        - 若文件缺失返回 `{}`；
        - 若存在以类名推断的节（去掉 "Config" 后缀并小写），优先读取该节；
        - 否则读取顶层平铺字段；
        - 仅返回与当前模型字段同名的键值对。
        """
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
    def from_yaml(cls, path: str | None = None) -> BaseConfig:
        """从 YAML 文件加载并实例化当前配置模型。

        返回当前配置模型的实例；当文件缺失或字段缺失时，按照 Pydantic 模型校验规则处理。
        如模型包含必填字段而 YAML 未提供，将抛出校验异常。
        若需要字典形式，请使用 `from_yaml_dict`。
        """
        data = cls.from_yaml_dict(path)
        return cls(**data)
