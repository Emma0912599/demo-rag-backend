"""数据库连接和操作模块"""

from typing import ClassVar
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from src.config import BaseConfig


class DatabaseConfig(BaseConfig):
    """数据库连接配置"""
    mongo_uri: str
    db_name: str
    yaml_section: ClassVar[str] = "database"

# 创建一个全局的数据库配置实例
db_config = DatabaseConfig.from_yaml()

# 创建一个全局的 MongoClient 实例，以便在整个应用中复用
client = MongoClient(db_config.mongo_uri)

def get_db() -> Database:
    """获取数据库实例"""
    return client[db_config.db_name]

def get_users_collection():
    """获取用户集合"""
    db = get_db()
    return db.users

def get_chat_history_collection():
    """获取聊天记录集合"""
    db = get_db()
    return db.chat_history