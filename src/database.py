"""数据库连接和操作模块"""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# 直接从 config 模块导入配置实例
from src.config import db_config

_client: MongoClient | None = None
_db: Database | None = None


def get_db() -> Database:
    """获取数据库实例，如果不存在则创建新的连接"""
    global _client, _db
    if _db is None:
        if not db_config.mongo_uri or not db_config.db_name:
            raise ValueError("MongoDB URI and DB name must be set in config.yaml")
        _client = MongoClient(db_config.mongo_uri)
        _db = _client[db_config.db_name]
    return _db


def get_users_collection() -> Collection:
    """获取用于存储用户信息的 'users' 集合"""
    db = get_db()
    return db["users"]