"""用户数据持久化"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from src.database import get_users_collection


class UserProfile(BaseModel):
    """用户个人资料数据模型，用于验证和处理前端发送的用户信息"""

    name: str = "test"
    birthday: Optional[date] = None
    occupation: Optional[str] = None
    hobby: List[str] = Field(default_factory=list)
    self_description: Optional[str] = None


def save_user_profile(user_profile: UserProfile) -> str:
    """
    将用户个人资料创建或更新到 MongoDB (Upsert).
    - 如果用户 `name` 不存在，则创建新文档.
    - 如果用户 `name` 已存在，则增量更新文档.

    Args:
        user_profile: 经过验证的用户个人资料数据. `name` 字段在此操作中是必需的.

    Returns:
        存储或更新的文档的 ID.

    Raises:
        ValueError: 如果 `user_profile.name` 未提供.
    """
    if not user_profile.name:
        raise ValueError("User 'name' is required to save or update a profile.")

    collection = get_users_collection()

    user_data = user_profile.model_dump(exclude_unset=True, mode="json")

    result = collection.update_one(
        {"name": user_profile.name},
        {"$set": user_data},
        upsert=True
    )

    if result.upserted_id:
        return str(result.upserted_id)
    else:
        updated_document = collection.find_one(
            {"name": user_profile.name},
            {"_id": 1}  
        )
        if updated_document:
            return str(updated_document["_id"])
        else:
            raise RuntimeError(f"Failed to find user '{user_profile.name}' after update.")
