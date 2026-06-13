"""
Action Engine — 微行为引擎

§3.2 设计文档：
  将语言互动拆解为"不可能失败"的微行为
  - 最小行为单元 < 30 秒
  - 3 次点击完成
  - 零挫败保障（任何时候可跳过/换一条）

行为类型：
  read_one_post      — 读完一条资讯（10-60秒）
  listen_one_min     — 听一段30秒音频
  say_one_thing      — 跟读/复述一句话
  write_one_sentence — 写一句话（日记/评论/想法）
  look_up_one        — 查一个不认识的词
"""
import uuid
import random
from datetime import datetime, timezone, date
from typing import Optional
from loguru import logger
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.habit import (
    MicroHabitLog, DailyInfoFeed, VariableReward, LanguageAsset, GrowthMilestone,
)
from src.models.user import User


# ── 行为类型定义 ──

HABIT_CODES = {
    "read_one_post": {
        "name": "读一条资讯",
        "default_duration": 30,
        "base_xp": 5,
        "icon": "📰",
        "description": "读完一条英文资讯",
    },
    "listen_one_min": {
        "name": "听一段音频",
        "default_duration": 30,
        "base_xp": 5,
        "icon": "🎧",
        "description": "听一段30秒英文音频",
    },
    "say_one_thing": {
        "name": "跟读一句话",
        "default_duration": 10,
        "base_xp": 8,
        "icon": "🎤",
        "description": "跟读/复述一句话",
    },
    "write_one_sentence": {
        "name": "写一句话",
        "default_duration": 60,
        "base_xp": 10,
        "icon": "✍️",
        "description": "写一句话（日记/评论/想法）",
    },
    "look_up_one": {
        "name": "查一个词",
        "default_duration": 15,
        "base_xp": 3,
        "icon": "🔍",
        "description": "查一个不认识的词",
    },
}


class ActionEngine:
    """微行为引擎"""

    @staticmethod
    def get_habit_info(habit_code: str) -> Optional[dict]:
        """获取行为类型信息"""
        return HABIT_CODES.get(habit_code)

    @staticmethod
    def list_available_habits() -> dict:
        """列出所有可用行为"""
        return HABIT_CODES

    @staticmethod
    def calculate_xp(habit_code: str, duration_seconds: int = 0, streak_bonus: int = 0) -> int:
        """
        计算经验值

        公式: base_xp * (1 + duration_bonus + streak_bonus)
          - base_xp: 基础经验
          - duration_bonus: 超出默认时长的额外加成（最多 +50%）
          - streak_bonus: 连续天数加成（每连续7天 +10%，最多 +50%）
        """
        info = HABIT_CODES.get(habit_code)
        if not info:
            return 0

        base = info["base_xp"]
        default_dur = info["default_duration"]

        # 时长加成
        if duration_seconds > default_dur and default_dur > 0:
            ratio = duration_seconds / default_dur
            duration_bonus = min(0.5, ratio * 0.1)  # 每多10%时长加1%加成，最多50%
        else:
            duration_bonus = 0

        # 连续加成
        streak_mult = 1 + min(0.5, streak_bonus * 0.1)  # 每7天+10%，最多+50%

        xp = int(base * (1 + duration_bonus) * streak_mult)
        return max(xp, 1)  # 至少1点

    async def record_habit(
        self,
        user_id: str,
        habit_code: str,
        duration_seconds: int = 0,
        completion_status: str = "completed",
        triggered_by: str = "trigger_engine",
        feed_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """
        记录一个微行为

        返回：{ "habit_log_id": str, "xp_earned": int, "streak_days": int, "reward": Optional[dict] }
        """
        if habit_code not in HABIT_CODES:
            raise ValueError(f"未知行为类型: {habit_code}")

        async with db or AsyncSessionLocal() as session:
            # 获取用户当前 streak
            streak_days = await self._get_streak(session, user_id)

            # 计算 XP
            xp = self.calculate_xp(habit_code, duration_seconds, streak_days // 7)

            # 创建日志
            log = MicroHabitLog(
                user_id=user_id,
                habit_code=habit_code,
                triggered_by=triggered_by,
                duration_seconds=duration_seconds or HABIT_CODES[habit_code]["default_duration"],
                completion_status=completion_status,
                xp_earned=xp,
                feed_id=feed_id,
            )
            session.add(log)

            # 更新用户 XP
            await self._add_xp_to_profile(session, user_id, xp)

            # 更新 streak
            await self._update_streak(session, user_id)

            # 更新关联的信息流状态
            if feed_id and completion_status != "skipped":
                await self._update_feed_interaction(session, feed_id, habit_code)

            await session.commit()

            # 检查是否需要触发可变奖励（每3个行为）
            recent_count = await self._count_recent_habits(session, user_id)
            reward = None
            if recent_count % 3 == 0:
                # 触发可变奖励（由 RewardEngine 处理）
                from src.engine.reward_engine import RewardEngine
                reward = await RewardEngine().try_grant_reward(user_id, session)

            return {
                "habit_log_id": log.id,
                "xp_earned": xp,
                "streak_days": streak_days,
                "total_habits_today": recent_count,
                "reward": reward,
            }

    async def get_today_summary(self, user_id: str) -> dict:
        """获取今日行为摘要"""
        async with AsyncSessionLocal() as session:
            today = date.today()
            stmt = select(MicroHabitLog).where(
                MicroHabitLog.user_id == user_id,
                func.date(MicroHabitLog.created_at) == today,
            )
            result = await session.execute(stmt)
            logs = result.scalars().all()

            total_xp = sum(l.xp_earned for l in logs)
            by_type = {}
            for l in logs:
                by_type[l.habit_code] = by_type.get(l.habit_code, 0) + 1

            return {
                "total_habits": len(logs),
                "total_xp": total_xp,
                "by_type": by_type,
                "streak_days": await self._get_streak(session, user_id),
            }

    # ── 内部方法 ──

    async def _get_streak(self, session: AsyncSession, user_id: str) -> int:
        """获取用户连续天数"""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        return profile.streak_days if profile else 0

    async def _add_xp_to_profile(self, session: AsyncSession, user_id: str, xp: int):
        """为用户添加成长 XP（自动创建用户）"""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            profile = User(id=user_id, username=user_id[:20])
            session.add(profile)
        profile.growth_xp = (profile.growth_xp or 0) + xp
        # 检查是否需要升级
        await self._check_level_up(session, profile)

    async def _check_level_up(self, session: AsyncSession, profile: User):
        """检查等级提升（每100XP升一级）"""
        xp = profile.growth_xp or 0
        new_level = (xp // 100) + 1
        if new_level > (profile.habit_level or 1):
            profile.habit_level = new_level
            logger.info(f"用户 {profile.id[:8]} 习惯等级提升到 {new_level}")

    async def _update_streak(self, session: AsyncSession, user_id: str):
        """更新连续天数"""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            return

        today = date.today()
        if profile.last_feed_date:
            # 如果 last_feed_date 是昨天 → streak +1
            if profile.last_feed_date == today:
                return  # 今天已更新过
            from datetime import timedelta
            if profile.last_feed_date == today - timedelta(days=1):
                profile.streak_days = (profile.streak_days or 0) + 1
            else:
                # 断了，重置
                profile.streak_days = 1
        else:
            profile.streak_days = 1

        profile.last_feed_date = today

    async def _update_feed_interaction(self, session: AsyncSession, feed_id: str, habit_code: str):
        """更新信息流的交互状态"""
        stmt = select(DailyInfoFeed).where(DailyInfoFeed.id == feed_id)
        result = await session.execute(stmt)
        feed = result.scalar_one_or_none()
        if feed:
            interaction_map = {
                "read_one_post": "read",
                "listen_one_min": "listened",
                "say_one_thing": "responded",
                "write_one_sentence": "responded",
                "look_up_one": "read",
            }
            feed.user_interaction = interaction_map.get(habit_code, "read")

    async def _count_recent_habits(self, session: AsyncSession, user_id: str) -> int:
        """统计当日行为数"""
        today = date.today()
        stmt = select(func.count(MicroHabitLog.id)).where(
            MicroHabitLog.user_id == user_id,
            func.date(MicroHabitLog.created_at) == today,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0