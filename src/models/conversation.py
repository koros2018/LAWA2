"""
LAWA2 对话模型 v5.0.0
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from src.database.main import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    """对话记录"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("lawa2_users.id"), nullable=False, index=True)
    partner_id = Column(Integer, nullable=True, comment="语伴ID（AI对话为None）")
    topic = Column(String(500), nullable=True, comment="对话主题")
    word_count = Column(Integer, default=0, comment="总词汇量")
    level = Column(Integer, default=1, comment="对话等级 1-5")
    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages_list = relationship("ConversationMessage", back_populates="conversation", lazy="selectin", order_by="ConversationMessage.order")


class ConversationMessage(Base):
    """对话消息"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, comment="user|assistant|system")
    content = Column(Text, nullable=False, comment="中文内容")
    content_en = Column(Text, nullable=True, comment="英文内容")
    order = Column(Integer, nullable=False, comment="消息顺序")
    created_at = Column(DateTime, default=_utcnow)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages_list")


class Correction(Base):
    """纠错记录"""
    __tablename__ = "corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    original = Column(Text, nullable=False, comment="用户原始输入")
    corrected = Column(Text, nullable=False, comment="纠错后内容")
    explanation = Column(Text, nullable=True, comment="纠错说明")
    word_diff = Column(JSON, default=dict, comment="词汇差异")
    created_at = Column(DateTime, default=_utcnow)