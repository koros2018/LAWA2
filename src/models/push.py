"""
LAWA2 — 推送通知数据模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from datetime import datetime, timezone
import uuid

from src.database.main import Base


class PushNotification(Base):
    """推送通知记录"""
    __tablename__ = "push_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    body_en = Column(Text, nullable=True)
    notification_type = Column(String(50), nullable=False, default="reminder")
    related_event_id = Column(String(36), nullable=True)
    is_read = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scheduled_at = Column(DateTime(timezone=True), nullable=True)


class PushPreference(Base):
    """用户推送偏好"""
    __tablename__ = "push_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True, unique=True, nullable=False)
    push_enabled = Column(Boolean, default=True)
    reminder_push = Column(Boolean, default=True)
    holiday_push = Column(Boolean, default=True)
    culture_egg_push = Column(Boolean, default=True)
    milestone_push = Column(Boolean, default=True)
    daily_feed_push = Column(Boolean, default=True)
    morning_time = Column(String(5), default="08:00")
    noon_time = Column(String(5), default="12:30")
    evening_time = Column(String(5), default="20:00")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))