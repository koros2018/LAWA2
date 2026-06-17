from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.database.main import Base


def _utcnow() -> datetime:
    return datetime.utcnow()


class SeedContent(Base):
    """种子语料管理 — 社交场景、推送文案、文化背景等"""

    __tablename__ = "seed_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 内容类型
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # content_type: social_scene | push_message | culture_tip | holiday_info | vocabulary_card

    # 内容字段
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=True)
    content_en: Mapped[str] = mapped_column(Text, nullable=True)

    # 元数据
    tags: Mapped[str] = mapped_column(String(500), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=True)
    # difficulty: beginner | intermediate | advanced

    # 状态
    is_active: Mapped[bool] = mapped_column(default=True)
    is_system: Mapped[bool] = mapped_column(default=False)
    # is_system=True 表示系统内置，用户不可删除

    # 时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "title": self.title,
            "title_en": self.title_en,
            "content": self.content,
            "content_en": self.content_en,
            "tags": self.tags.split(",") if self.tags else [],
            "difficulty": self.difficulty,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
