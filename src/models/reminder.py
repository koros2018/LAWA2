"""LAWA2 事项提醒 Agent — 数据模型"""
from datetime import date, datetime, timezone
from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database.main import Base


class ReminderEvent(Base):
    """提醒事件"""
    __tablename__ = "lawa2_reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    
    # 标题（双语）
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # 日期
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # 类型：personal / holiday / todo / anniversary
    event_type: Mapped[str] = mapped_column(String(20), default="personal", index=True)
    
    # 备注（双语）
    note: Mapped[str] = mapped_column(Text, nullable=True)
    note_en: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 文化背景（仅节假日用）
    culture_background: Mapped[str] = mapped_column(Text, nullable=True)
    culture_background_en: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 状态
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_rule: Mapped[str] = mapped_column(String(50), nullable=True)  # yearly / monthly / weekly
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
