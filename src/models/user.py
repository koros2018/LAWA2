"""LAWA2 用户模型"""
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, JSON, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.main import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """用户主表"""
    __tablename__ = "lawa2_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 语言
    native_lang: Mapped[str] = mapped_column(String(5), default="zh")
    learn_lang: Mapped[str] = mapped_column(String(5), default="en")
    current_level: Mapped[str] = mapped_column(String(5), nullable=True)
    target_level: Mapped[str] = mapped_column(String(5), nullable=True)
    
    # 学习风格
    interests: Mapped[str] = mapped_column(JSON, default=list)
    
    # 习惯引擎专用字段
    growth_xp: Mapped[int] = mapped_column(Integer, default=0)
    habit_level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_feed_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    
    # 双向桥梁
    bridge_level: Mapped[int] = mapped_column(Integer, default=0)
    
    # 元数据
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)

    # 关系
    conversations = relationship("Conversation", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User {self.username} lvl={self.habit_level} xp={self.growth_xp}>"
