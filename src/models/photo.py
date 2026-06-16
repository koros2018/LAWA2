"""
LAWA2 — 拍照理解数据模型

用户拍照上传 → AI 理解 → 中英对话
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class PhotoUnderstanding(Base):
    """拍照理解记录"""
    __tablename__ = "photo_understandings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_path: Mapped[str] = mapped_column(String(512), default="")

    # AI 理解结果（中英双语）
    ai_description: Mapped[str] = mapped_column(Text, default="")
    ai_description_en: Mapped[str] = mapped_column(Text, default="")

    # 关键词提取
    extracted_words: Mapped[dict] = mapped_column(JSON, default=list)

    # 场景标签
    scene_tags: Mapped[list] = mapped_column(JSON, default=list)

    # 元数据
    original_filename: Mapped[str] = mapped_column(String(256), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(64), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # 对话计数
    chat_count: Mapped[int] = mapped_column(Integer, default=0)


class PhotoChat(Base):
    """基于图片的对话"""
    __tablename__ = "photo_chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id: Mapped[str] = mapped_column(String(36), ForeignKey("photo_understandings.id"), index=True, nullable=False)

    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, default="")
    content_en: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)