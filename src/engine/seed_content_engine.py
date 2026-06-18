"""
LAWA2 — 种子语料管理引擎

内容类型：
- social_scene: 社交场景语料
- push_message: 推送通知文案
- culture_tip: 文化背景提示
- holiday_info: 节假日信息
- vocabulary_card: 词汇卡片
"""

from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.seed_content import SeedContent
from src.models.user import User
from datetime import datetime
from typing import Optional
from loguru import logger


class SeedContentEngine:
    """种子语料管理引擎"""

    @staticmethod
    async def list_contents(
        db: AsyncSession,
        user_id: int,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SeedContent], int]:
        """列出种子语料"""
        stmt = select(SeedContent).where(SeedContent.user_id == user_id)

        if content_type:
            stmt = stmt.where(SeedContent.content_type == content_type)

        if is_active is not None:
            stmt = stmt.where(SeedContent.is_active == is_active)

        if search:
            stmt = stmt.where(
                (SeedContent.title.ilike(f"%{search}%")) |
                (SeedContent.title_en.ilike(f"%{search}%")) |
                (SeedContent.content.ilike(f"%{search}%"))
            )

        total_stmt = select(func.count(SeedContent.id)).where(SeedContent.user_id == user_id)
        if content_type:
            total_stmt = total_stmt.where(SeedContent.content_type == content_type)
        if is_active is not None:
            total_stmt = total_stmt.where(SeedContent.is_active == is_active)
        if search:
            total_stmt = total_stmt.where(
                (SeedContent.title.ilike(f"%{search}%")) |
                (SeedContent.title_en.ilike(f"%{search}%")) |
                (SeedContent.content.ilike(f"%{search}%"))
            )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        stmt = stmt.order_by(SeedContent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        contents = result.scalars().all()

        return contents, total

    @staticmethod
    async def get_content(db: AsyncSession, user_id: int, content_id: int) -> Optional[SeedContent]:
        """获取单个种子语料"""
        stmt = select(SeedContent).where(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def create_content(
        db: AsyncSession,
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
        await db.commit()
        await db.refresh(content)
        return content

    @staticmethod
    async def update_content(
        db: AsyncSession,
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
        stmt = select(SeedContent).where(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
            SeedContent.is_system == False,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one()

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
        await db.commit()
        await db.refresh(existing)
        return existing

    @staticmethod
    async def delete_content(db: AsyncSession, user_id: int, content_id: int) -> bool:
        """删除种子语料"""
        stmt = select(SeedContent).where(
            SeedContent.id == content_id,
            SeedContent.user_id == user_id,
            SeedContent.is_system == False,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one()

        if not existing:
            return False

        await db.delete(existing)
        await db.commit()
        return True

    @staticmethod
    async def get_system_contents(db: AsyncSession, content_type: Optional[str] = None) -> list[SeedContent]:
        """获取系统内置种子语料"""
        stmt = select(SeedContent).where(SeedContent.is_system == True)

        if content_type:
            stmt = stmt.where(SeedContent.content_type == content_type)

        result = await db.execute(stmt.order_by(SeedContent.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_by_type(db: AsyncSession, user_id: int, content_type: str) -> list[SeedContent]:
        """按类型获取种子语料"""
        stmt = select(SeedContent).where(
            SeedContent.user_id == user_id,
            SeedContent.content_type == content_type,
            SeedContent.is_active == True,
        ).order_by(SeedContent.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
