"""
LAWA 词汇卡片数据模型

WordCard — 通用词汇卡片（独立于 companion 系统）
WordCardReview — 复习记录
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.main import Base


class WordCard(Base):
    """通用词汇卡片"""
    __tablename__ = "lawa2_word_cards"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("lawa2_users.id"), nullable=False, index=True)

    word: Mapped[str] = mapped_column(String(200), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), default="en")  # en | zh

    # 释义
    definition: Mapped[str] = mapped_column(Text, nullable=True)
    definition_native: Mapped[str] = mapped_column(Text, nullable=True)  # 母语释义

    # 词性 / 音标
    part_of_speech: Mapped[str] = mapped_column(String(30), nullable=True)
    phonetic: Mapped[str] = mapped_column(String(100), nullable=True)

    # 例句
    example_sentence: Mapped[str] = mapped_column(Text, nullable=True)
    example_translation: Mapped[str] = mapped_column(Text, nullable=True)

    # 来源
    source: Mapped[str] = mapped_column(String(30), default="manual")  # manual | bridge | feed | photo | companion
    source_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # 标签
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array, e.g. ["daily", "business"]

    # 难度 (1-5)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)

    # 间隔复习 (SM-2)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    review_interval_hours: Mapped[float] = mapped_column(Float, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    last_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False)

    # 收藏状态
    is_favorited: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "word", "lang", name="uq_word_card"),
    )


class WordCardReview(Base):
    """词汇卡片复习记录"""
    __tablename__ = "lawa2_word_card_reviews"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("lawa2_word_cards.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("lawa2_users.id"), nullable=False, index=True)

    quality: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-5
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    card: Mapped["WordCard"] = relationship()