from fastapi import APIRouter
from app.api.v1 import users, students, subjects, chat, table_formats, conduct
from app.api.v1 import db_admin
from app.auth.router import router as auth_router

router = APIRouter()

# Health check
@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "成績管理系統運行中"}

# Auth
router.include_router(auth_router)

# Resources
router.include_router(users.router)
router.include_router(students.router)
router.include_router(subjects.router)

# Chat
router.include_router(chat.router)

# Table Formats
router.include_router(table_formats.router)

# Conduct (德育管理)
router.include_router(conduct.router)

# DB Admin
router.include_router(db_admin.router)