"""
表格格式模板模型
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TableFormatTemplate(Base):
    __tablename__ = "table_format_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 模板名稱
    description: Mapped[str] = mapped_column(String(500), nullable=True)  # 模板描述
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 類型：draft_list/ranking/makeup_suggestion/custom
    columns_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # 欄位設定
    style_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # 樣式設定
    fail_threshold: Mapped[float] = mapped_column(default=60.0)  # 及格分數線
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否為預設模板
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否啟用
    created_by: Mapped[int] = mapped_column(nullable=True)  # 建立者ID
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_default_template(cls, template_type: str, db):
        """取得指定類型的預設模板"""
        return db.query(cls).filter(
            cls.template_type == template_type,
            cls.is_default == True,
            cls.is_active == True
        ).first()

    @classmethod
    def get_all_active(cls, db):
        """取得所有啟用的模板"""
        return db.query(cls).filter(cls.is_active == True).order_by(cls.name).all()