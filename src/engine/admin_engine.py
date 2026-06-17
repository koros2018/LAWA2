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
from src.models.habit import MicroHabitLog, UserHabitConfig, BridgeInteraction
from src.models.photo import PhotoUnderstanding
from src.models.reminder import ReminderEvent
from src.models.push import PushNotification
from datetime import timedelta


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
        today = datetime.now(timezone.utc).date()
        
        # ── 基础统计 ──
        user_count = await self.get_user_count(db)
        active_result = await db.execute(
            select(func.count(func.distinct(MicroHabitLog.user_id)))
            .where(func.date(MicroHabitLog.created_at) == today)
        )
        active_users = active_result.scalar() or 0
        
        event_result = await db.execute(select(func.count(MicroHabitLog.id)))
        total_events = event_result.scalar() or 0
        
        today_event_result = await db.execute(
            select(func.count(MicroHabitLog.id))
            .where(func.date(MicroHabitLog.created_at) == today)
        )
        today_events = today_event_result.scalar() or 0
        
        config_result = await db.execute(
            select(func.count(UserHabitConfig.user_id))
            .where(UserHabitConfig.feed_enabled == True)
        )
        active_configs = config_result.scalar() or 0
        
        # ── 新增：7日趋势 ──
        daily_trends = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_result = await db.execute(
                select(func.count(func.distinct(MicroHabitLog.user_id)))
                .where(func.date(MicroHabitLog.created_at) == day)
            )
            day_active = day_result.scalar() or 0
            day_events = await db.execute(
                select(func.count(MicroHabitLog.id))
                .where(func.date(MicroHabitLog.created_at) == day)
            )
            daily_trends.append({
                "date": day.isoformat(),
                "active_users": day_active,
                "events": day_events.scalar() or 0,
            })
        
        # ── 新增：Top 10 用户（按 XP） ──
        top_users_stmt = select(User).where(User.is_active == True).order_by(
            User.growth_xp.desc()
        ).limit(10)
        top_users_result = (await db.execute(top_users_stmt)).scalars().all()
        top_users = [self._user_to_dict(u) for u in top_users_result]
        
        # ── 新增： engagement 指标 ──
        avg_events = (total_events / user_count) if user_count > 0 else 0
        
        # 新增用户（近7天）
        week_ago = today - timedelta(days=7)
        new_users = await db.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        new_users_count = new_users.scalar() or 0
        
        # 桥接互动总数
        bridge_stmt = select(func.count(BridgeInteraction.id))
        bridge_total = (await db.execute(bridge_stmt)).scalar() or 0
        
        # 照片总数
        photo_stmt = select(func.count(PhotoUnderstanding.id))
        photo_total = (await db.execute(photo_stmt)).scalar() or 0
        
        # 提醒总数
        reminder_stmt = select(func.count(ReminderEvent.id))
        reminder_total = (await db.execute(reminder_stmt)).scalar() or 0
        
        # 推送通知总数
        push_stmt = select(func.count(PushNotification.id))
        push_total = (await db.execute(push_stmt)).scalar() or 0
        
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
            # ── 新增字段 ──
            "daily_trends": daily_trends,
            "top_users": top_users,
            "avg_events_per_user": round(avg_events, 2),
            "new_users_7d": new_users_count,
            "bridge_interactions": bridge_total,
            "photos": photo_total,
            "reminders": reminder_total,
            "push_notifications": push_total,
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
