"""
中學成績管理系統 - 後端服務
AI Agent 驅動的成績管理系統
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.database import init_db
from app.api.routes import router as api_router

load_dotenv()

app = FastAPI(
    title="成績管理系統 API",
    description="中學成績管理系統 - AI Agent 驅動",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    init_db()
    # 技能已在 app.skills.registry 模組載入時自動註冊


@app.get("/")
async def root():
    return {
        "message": "成績管理系統 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# CORS
origins = os.getenv("CORS_ORIGINS", '["*"]')
import ast
origins_list = ast.literal_eval(origins) if isinstance(origins, str) else origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1", tags=["api"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)