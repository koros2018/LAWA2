"""
Admin Engine — 超级管理员引擎

功能：
  - 用户管理（列表/搜索/详情）
  - 系统统计数据
  - 种子内容管理
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.user import User
from src.models.habit import MicroHabitLog, UserHabitConfig


class AdminEngine:
    """管理员引擎"""

    async def get_users(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """获取用户列表"""
        query = select(User).order_by(User.created_at.desc())

        if search:
            query = query.where(
                User.username.ilike(f"%{search}%") |
                User.display_name.ilike(f"%{search}%")
            )

        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        users = result.scalars().all()

        return [self._user_to_dict(u) for u in users]

    async def get_user_count(self, db: AsyncSession) -> int:
        """获取用户总数"""
        result = await db.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def get_user_detail(self, user_id: str, db: AsyncSession) -> Optional[dict]:
        """获取用户详情"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return self._user_to_dict(user)

    async def toggle_user_active(self, user_id: str, db: AsyncSession) -> Optional[dict]:
        """切换用户激活状态"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        user.is_active = not user.is_active
        await db.commit()
        await db.refresh(user)
        return self._user_to_dict(user)

    async def get_system_stats(self, db: AsyncSession) -> dict:
        """获取系统统计数据"""
        # 用户总数
        user_count = await self.get_user_count(db)

        # 今日活跃用户（有今日 habit_event 的用户）
        today = datetime.now(timezone.utc).date()
        active_result = await db.execute(
            select(func.count(func.distinct(MicroHabitLog.user_id)))
            .where(func.date(MicroHabitLog.created_at) == today)
        )
        active_users = active_result.scalar() or 0

        # 习惯事件总数
        event_result = await db.execute(select(func.count(MicroHabitLog.id)))
        total_events = event_result.scalar() or 0

        # 今日习惯事件数
        today_event_result = await db.execute(
            select(func.count(MicroHabitLog.id))
            .where(func.date(MicroHabitLog.created_at) == today)
        )
        today_events = today_event_result.scalar() or 0

        # 活跃配置数
        config_result = await db.execute(
            select(func.count(UserHabitConfig.user_id))
            .where(UserHabitConfig.feed_enabled == True)
        )
        active_configs = config_result.scalar() or 0

        # 数据库大小
        db_size = 0
        try:
            size_result = await db.execute(text("SELECT page_count * page_size FROM pragma_page_count, pragma_page_size"))
            row = size_result.fetchone()
            if row:
                db_size = row[0]
        except Exception:
            pass

        return {
            "user_count": user_count,
            "active_users_today": active_users,
            "total_habit_events": total_events,
            "today_habit_events": today_events,
            "active_configs": active_configs,
            "db_size_bytes": db_size,
        }

    def _user_to_dict(self, user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "native_lang": user.native_lang,
            "learn_lang": user.learn_lang,
            "current_level": user.current_level,
            "habit_level": user.habit_level,
            "growth_xp": user.growth_xp,
            "streak_days": user.streak_days,
            "bridge_level": user.bridge_level,
            "is_active": user.is_active,
            "interests": user.interests or [],
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }


# 全局单例
admin_engine = AdminEngine()
