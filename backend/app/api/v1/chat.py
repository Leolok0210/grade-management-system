from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json, os, uuid
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.audit import Conversation
from app.skills.base import UserContext, SkillResult
from app.skills.orchestrator import AgentOrchestrator
from app.ai.router import MultiModelRouter

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")

def ensure_upload_export_dirs():
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)
    except OSError:
        pass  # Vercel read-only filesystem

ensure_upload_export_dirs()

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

    conv_id = conv.id
    history = conv.messages or []
    history.append({"role": "user", "content": req.message})

    async def event_generator():
        full_content = ""
        async for event in _orchestrator.handle_message_stream(req.message, history[:-1], context, db):
            sse_data = {"type": event.type}
            if event.data:
                sse_data.update(event.data)
            full_content += sse_data.get("text", "")
            yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

        # 儲存對話
        history.append({"role": "assistant", "content": full_content})
        conv.messages = history
        conv.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class ConversationItem(BaseModel):
    id: int
    updated_at: Optional[str] = None
    preview: str

class ConversationDetail(BaseModel):
    id: int
    messages: list[dict]
    updated_at: Optional[str] = None


@router.get("/conversations", response_model=List[ConversationItem])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    items = []
    for c in convs:
        msgs = c.messages or []
        preview = ""
        for m in reversed(msgs):
            if m.get("role") == "user" and m.get("content"):
                preview = m["content"][:50]
                break
        items.append(ConversationItem(
            id=c.id,
            updated_at=c.updated_at.isoformat() if c.updated_at else None,
            preview=preview,
        ))
    return items


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
async def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="對話不存在")
    return ConversationDetail(
        id=conv.id,
        messages=conv.messages or [],
        updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
    )


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="只支援 .xlsx / .xls / .csv 檔案")
    file_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    return UploadResponse(file_id=file_id, filename=file.filename, size=len(content))


@router.get("/export/{file_id}")
async def download_export(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    from fastapi.responses import FileResponse
    if not file_id.isalnum():
        raise HTTPException(status_code=400, detail="無效的檔案ID")
    for fname in os.listdir(EXPORT_DIR):
        if fname.startswith(file_id) or file_id in fname:
            return FileResponse(
                os.path.join(EXPORT_DIR, fname),
                filename=fname,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    raise HTTPException(status_code=404, detail="檔案不存在")