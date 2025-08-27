import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import (
    app_config,
    cors_config,
    init_logging,
)
from src.core.api import router as api_router

# Initialize logging
init_logging()

app = FastAPI(
    title=app_config.name,
    version=app_config.version,
    root_path=app_config.root_path,
)

# === 调试修改 ===

# # Add CORS middleware
# if not cors_config.origins:
#     raise RuntimeError(
#         "CORS origins are not configured. "
#         "Please check if `config.yaml` is present and the `cors.origins` section is correct."
#     )
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[str(origin) for origin in cors_config.origins],
#     allow_credentials=True,
#     allow_methods=cors_config.methods,
#     allow_headers=cors_config.headers,
# )

# 直接使用写死的（Hardcoded）配置来代替
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
