"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.api import router as api_router
from src.cache import LocalCache, RedisCache
from src.config import BaseConfig

logger = logging.getLogger(__name__)


class RedisConfig(BaseConfig):
    yaml_section = "redis"
    host: str = "localhost"
    port: int = 6379


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        config = RedisConfig.from_yaml()
        app.state.cache = RedisCache(config=config)
    except Exception as e:
        logger.warning(f"Failed to initialize RedisCache: {e}, falling back to LocalCache")
        app.state.cache = LocalCache()
    try:
        yield
    finally:
        if hasattr(app.state, "cache"):
            await app.state.cache.close()


app = FastAPI(title="demo-rag-backend", lifespan=lifespan)

# 配置 CORS 中间件
origins = [
    "http://localhost:8080", 
    "http://127.0.0.1:8080", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(api_router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
