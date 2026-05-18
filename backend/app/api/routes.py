from fastapi import APIRouter
from app.api.v1 import users, students, subjects, chat
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