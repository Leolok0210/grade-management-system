"""
表格格式模板 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.models.table_format import TableFormatTemplate

router = APIRouter(prefix="/table-formats", tags=["表格格式管理"])


class TableFormatBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: str
    columns_config: dict
    style_config: dict
    fail_threshold: float = 60.0
    is_default: bool = False


class TableFormatCreate(TableFormatBase):
    pass


class TableFormatUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    columns_config: Optional[dict] = None
    style_config: Optional[dict] = None
    fail_threshold: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class TableFormatResponse(TableFormatBase):
    id: int
    is_active: bool
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TableFormatResponse])
async def list_templates(
    template_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得所有表格格式模板"""
    query = db.query(TableFormatTemplate).filter(TableFormatTemplate.is_active == True)
    if template_type:
        query = query.filter(TableFormatTemplate.template_type == template_type)
    return query.order_by(TableFormatTemplate.name).all()


@router.get("/{template_id}", response_model=TableFormatResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得特定模板"""
    template = db.query(TableFormatTemplate).filter(TableFormatTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("", response_model=TableFormatResponse)
async def create_template(
    template: TableFormatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """建立新模板（需要管理員權限）"""
    # 如果設為預設，先取消其他同類型的預設
    if template.is_default:
        db.query(TableFormatTemplate).filter(
            TableFormatTemplate.template_type == template.template_type
        ).update({"is_default": False})

    db_template = TableFormatTemplate(
        **template.model_dump(),
        created_by=current_user.id,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.put("/{template_id}", response_model=TableFormatResponse)
async def update_template(
    template_id: int,
    update_data: TableFormatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """更新模板（需要管理員權限）"""
    template = db.query(TableFormatTemplate).filter(TableFormatTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_dict = update_data.model_dump(exclude_unset=True)

    # 如果設為預設，先取消其他同類型的預設
    if update_dict.get("is_default"):
        db.query(TableFormatTemplate).filter(
            TableFormatTemplate.template_type == template.template_type,
            TableFormatTemplate.id != template_id,
        ).update({"is_default": False})

    for key, value in update_dict.items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """刪除模板（軟刪除，設為非啟用）"""
    template = db.query(TableFormatTemplate).filter(TableFormatTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template.is_active = False
    db.commit()
    return {"message": "模板已刪除"}


@router.post("/seed-defaults")
async def seed_default_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """建立預設模板（初始化用）"""
    default_templates = [
        {
            "name": "草榜標準格式",
            "description": "標準學期成績草榜，含不及格率、學生不及格次數統計",
            "template_type": "draft_list",
            "columns_config": {
                "header_row": ["科目", "測驗名稱", "測驗日期", "負責老師", "不及格率"],
                "student_columns": ["學生編號", "班級", "姓名", "學號"],
                "data_columns": "auto",  # 自動從成績資料產生
                "summary_column": "不及格測驗次數",
            },
            "style_config": {
                "fail_score_bg": "#ffcccc",
                "fail_count_bg": "#ff9999",
                "fail_count_style": {"font-weight": "bold", "font-style": "italic"},
                "pass_rate_style": {"font-weight": "bold"},
            },
            "fail_threshold": 60.0,
            "is_default": True,
        },
        {
            "name": "學生排名格式",
            "description": "依總分/平均分排名，含排名欄位",
            "template_type": "ranking",
            "columns_config": {
                "header_row": ["排名", "學號", "姓名", "班級"],
                "data_columns": "auto",
                "summary_column": "總分",
            },
            "style_config": {
                "rank_style": {"font-weight": "bold", "color": "#667eea"},
                "top_n_bg": "#e8f4ff",
            },
            "fail_threshold": 60.0,
            "is_default": True,
        },
        {
            "name": "補考建議格式",
            "description": "不及格學生及補考科目建議",
            "template_type": "makeup_suggestion",
            "columns_config": {
                "header_row": ["學號", "姓名", "班級", "不及格科目", "建議補考項目"],
                "data_columns": ["不及格次數", "需要補考科目列表"],
                "summary_column": "優先程度",
            },
            "style_config": {
                "urgent_bg": "#ffcccc",
                "warning_bg": "#fff3cd",
                "normal_bg": "#d4edda",
            },
            "fail_threshold": 60.0,
            "is_default": True,
        },
        {
            "name": "詳細分析格式",
            "description": "含平均分、標準差、異常偵測的詳細表格",
            "template_type": "analysis",
            "columns_config": {
                "header_row": ["學生", "平均分", "標準差", "異常標記", "排名"],
                "show_stats": True,
            },
            "style_config": {
                "anomaly_bg": "#ff9999",
                "normal_bg": "#ffffff",
            },
            "fail_threshold": 60.0,
            "is_default": False,
        },
    ]

    created = []
    for t in default_templates:
        # 檢查是否已存在
        existing = db.query(TableFormatTemplate).filter(
            TableFormatTemplate.template_type == t["template_type"],
            TableFormatTemplate.name == t["name"],
        ).first()
        if not existing:
            db_template = TableFormatTemplate(**t, created_by=current_user.id)
            db.add(db_template)
            created.append(t["name"])

    db.commit()
    return {"message": f"已建立 {len(created)} 個預設模板", "templates": created}