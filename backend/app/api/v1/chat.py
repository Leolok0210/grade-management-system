from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.audit import Conversation
from app.skills.base import UserContext, SkillResult
from app.skills.orchestrator import AgentOrchestrator
from app.ai.router import MultiModelRouter

router = APIRouter(prefix="/chat", tags=["聊天"])

# Singleton
_ai_router = MultiModelRouter()
_orchestrator = AgentOrchestrator(_ai_router)


class ChatMessage(BaseModel):
    conversation_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    data_card: Optional[dict] = None
    needs_confirm: bool = False
    confirm_request_id: Optional[str] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    req: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context = UserContext(
        user_id=current_user.id,
        name=current_user.name,
        role=current_user.role,
        school_id=current_user.school_id,
    )

    # 載入或建立對話
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()

    if not conv:
        conv = Conversation(user_id=current_user.id, messages=[])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 取得歷史
    history = conv.messages or []
    history.append({"role": "user", "content": req.message})

    # 呼叫 Orchestrator
    result = await _orchestrator.handle_message(req.message, history[:-1], context, db)

    # 處理結果
    if isinstance(result, SkillResult):
        reply = result.message
        data_card = result.data_card
    else:
        reply = result
        data_card = None

    # 儲存對話
    history.append({"role": "assistant", "content": reply})
    conv.messages = history
    conv.updated_at = __import__("datetime").datetime.utcnow()
    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply,
        data_card=data_card,
    )


@router.post("/message/stream")
async def send_message_stream(
    req: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context = UserContext(
        user_id=current_user.id,
        name=current_user.name,
        role=current_user.role,
        school_id=current_user.school_id,
    )

    # 載入或建立對話
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()

    if not conv:
        conv = Conversation(user_id=current_user.id, messages=[])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    history = conv.messages or []
    history.append({"role": "user", "content": req.message})

    async def event_generator():
        full_content = ""
        async for chunk in _orchestrator.handle_message_stream(req.message, history[:-1], context):
            data = {}
            if chunk.content:
                data["content"] = chunk.content
                full_content += chunk.content
            if chunk.tool_call_name:
                data["tool_call"] = chunk.tool_call_name
            if chunk.finish_reason:
                data["done"] = True

            if data:
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # 儲存對話
        history.append({"role": "assistant", "content": full_content})
        conv.messages = history
        conv.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")