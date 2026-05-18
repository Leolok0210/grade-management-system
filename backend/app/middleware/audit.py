"""
稽核日誌中介層 - 記錄所有技能執行
"""
from typing import Optional
from datetime import datetime
from app.models.audit import AuditLog


async def log_skill_execution(
    db,
    user_id: str,
    skill_name: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
):
    log = AuditLog(
        user_id=user_id,
        skill_name=skill_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(log)
    db.commit()