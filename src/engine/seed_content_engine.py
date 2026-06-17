"""
LAWA2 — 种子语料管理引擎

内容类型：
- social_scene: 社交场景语料
- push_message: 推送通知文案
- culture_tip: 文化背景提示
- holiday_info: 节假日信息
- vocabulary_card: 词汇卡片
"""

from sqlalchemy import and_
from sqlalchemy.orm import Session
from src.models.seed_content import SeedContent
from src.models.user import User
from datetime import datetime
from typing import Optional


class SeedContentEngine:
    """种子语料管理引擎"""

    @staticmethod
    def list_contents(
        db: Session,
        user_id: int,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SeedContent], int]:
        """列出种子语料"""
        query = db.query(SeedContent).filter(SeedContent.user_id == user_id)

        if content_type:
            query = query.filter(SeedContent.content_type == content_type)

        if is_active is not None:
            query = query.filter(SeedContent.is_active == is_active)

        if search:
            query = query.filter(
                (SeedContent.title.ilike(f"%{search}%")) |
                (SeedContent.title_en.ilike(f"%{search}%")) |
                (SeedContent.content.ilike(f"%{search}%"))
            )

        total = query.count()

        offset = (page - 1) * page_size
        contents = query.order_by(SeedContent.created_at.desc()).offset(offset).limit(page_size).all()

        return contents, total

    @staticmethod
    def get_content(db: Session, user_id: int, content_id: int) -> Optional[SeedContent]:
        """获取单个种子语料"""
        return db.query(SeedContent).filter(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
        ).first()

    @staticmethod
    def create_content(
        db: Session,
        user_id: int,
        content_type: str,
        title: str,
        title_en: str,
        content: Optional[str] = None,
        content_en: Optional[str] = None,
        tags: Optional[list[str]] = None,
        difficulty: Optional[str] = None,
        is_system: bool = False,
    ) -> SeedContent:
        """创建种子语料"""
        content = SeedContent(
            user_id=user_id,
            content_type=content_type,
            title=title,
            title_en=title_en,
            content=content,
            content_en=content_en,
            tags=",".join(tags) if tags else None,
            difficulty=difficulty,
            is_active=True,
            is_system=is_system,
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        return content

    @staticmethod
    def update_content(
        db: Session,
        user_id: int,
        content_id: int,
        title: Optional[str] = None,
        title_en: Optional[str] = None,
        content: Optional[str] = None,
        content_en: Optional[str] = None,
        tags: Optional[list[str]] = None,
        difficulty: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[SeedContent]:
        """更新种子语料"""
        existing = db.query(SeedContent).filter(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
            SeedContent.is_system == False,
        ).first()

        if not existing:
            return None

        if title is not None:
            existing.title = title
        if title_en is not None:
            existing.title_en = title_en
        if content is not None:
            existing.content = content
        if content_en is not None:
            existing.content_en = content_en
        if tags is not None:
            existing.tags = ",".join(tags)
        if difficulty is not None:
            existing.difficulty = difficulty
        if is_active is not None:
            existing.is_active = is_active

        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def delete_content(db: Session, user_id: int, content_id: int) -> bool:
        """删除种子语料"""
        existing = db.query(SeedContent).filter(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
            SeedContent.is_system == False,
        ).first()

        if not existing:
            return False

        db.delete(existing)
        db.commit()
        return True

    @staticmethod
    def get_system_contents(db: Session, content_type: Optional[str] = None) -> list[SeedContent]:
        """获取系统内置种子语料"""
        query = db.query(SeedContent).filter(SeedContent.is_system == True)

        if content_type:
            query = query.filter(SeedContent.content_type == content_type)

        return query.order_by(SeedContent.created_at.desc()).all()

    @staticmethod
    def get_by_type(db: Session, user_id: int, content_type: str) -> list[SeedContent]:
        """按类型获取种子语料"""
        return db.query(SeedContent).filter(
            SeedContent.user_id == user_id,
            SeedContent.content_type == content_type,
            SeedContent.is_active == True,
        ).order_by(SeedContent.created_at.desc()).all()
