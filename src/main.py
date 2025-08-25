"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.cache import LocalCache, RedisCache, RedisConfig
from src.core.api import router as core_router


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
        await app.state.cache.close()


app = FastAPI(title="demo-rag-backend", lifespan=lifespan)

app.include_router(core_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
