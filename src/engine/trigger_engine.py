"""
Trigger Engine — 触发引擎

§3.1 设计文档：
  在用户日常信息流中嵌入英文内容，触发学习行为
  - 早中晚三段推送（可配置时段）
  - 每次推送 < 3 分钟阅读量
  - 内容 90% 可理解 + 10% 略难
"""
import uuid
import random
from datetime import datetime, timezone, date
from typing import Optional, List
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.habit import DailyInfoFeed, UserHabitConfig
from src.models.user import User


# ── 种子内容库（本地初始内容，后续接入外部源）──

SEED_CONTENT = {
    "news_brief": [
        {
            "text": "AI learns to write poetry that humans can't distinguish from human-written poems.",
            "difficulty": "medium",
            "vocab_hints": ["metaphor", "distinguish", "artificial"],
            "source": "Tech Daily",
        },
        {
            "text": "Scientists discover a new species of frog in the Amazon rainforest.",
            "difficulty": "easy",
            "vocab_hints": ["species", "discover", "rainforest"],
            "source": "Nature News",
        },
        {
            "text": "The global push for renewable energy is accelerating faster than expected.",
            "difficulty": "medium",
            "vocab_hints": ["renewable", "accelerate", "global"],
            "source": "World Report",
        },
        {
            "text": "A new study shows that learning a second language can delay cognitive decline.",
            "difficulty": "medium",
            "vocab_hints": ["cognitive", "decline", "delay"],
            "source": "Science Weekly",
        },
        {
            "text": "The ancient art of calligraphy is making a comeback among young people.",
            "difficulty": "easy",
            "vocab_hints": ["calligraphy", "comeback", "ancient"],
            "source": "Culture Digest",
        },
    ],
    "social_post": [
        {
            "text": "Just finished reading '1984'. Still can't believe it was written in 1949. Some things never change.",
            "difficulty": "medium",
            "vocab_hints": ["propaganda", "surveillance", "dystopia"],
            "source": "Book Lovers",
        },
        {
            "text": "Hot take: pineapple on pizza is actually delicious and I will die on this hill 🍍🍕",
            "difficulty": "easy",
            "vocab_hints": ["hot take", "die on this hill"],
            "source": "Food Debate",
        },
        {
            "text": "The best productivity hack I've learned this year: do the hardest thing first, before checking email.",
            "difficulty": "easy",
            "vocab_hints": ["productivity", "hack"],
            "source": "Life Tips",
        },
    ],
    "fun_fact": [
        {
            "text": "Octopuses have three hearts. Two pump blood to the gills, one pumps it to the rest of the body.",
            "difficulty": "easy",
            "vocab_hints": ["octopus", "pump", "gill"],
            "source": "Animal Facts",
        },
        {
            "text": "The word 'uncopyrightable' is the longest English word that can be written without repeating any letter.",
            "difficulty": "medium",
            "vocab_hints": ["copyright", "repeating", "letter"],
            "source": "Word Trivia",
        },
        {
            "text": "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
            "difficulty": "easy",
            "vocab_hints": ["construction", "pyramid"],
            "source": "History Facts",
        },
    ],
    "vocab_card": [
        {
            "text": "serendipity (n.) — the occurrence of events by chance in a happy or beneficial way.",
            "difficulty": "hard",
            "vocab_hints": ["serendipity", "occurrence", "beneficial"],
            "source": "Word of the Day",
        },
        {
            "text": "ephemeral (adj.) — lasting for a very short time.",
            "difficulty": "medium",
            "vocab_hints": ["ephemeral", "transient", "fleeting"],
            "source": "Word of the Day",
        },
        {
            "text": "resilience (n.) — the capacity to recover quickly from difficulties.",
            "difficulty": "medium",
            "vocab_hints": ["resilience", "capacity", "recover"],
            "source": "Word of the Day",
        },
    ],
}


class TriggerEngine:
    """触发引擎 — 信息流推送"""

    async def get_feed(
        self,
        user_id: str,
        time_slot: str = "morning",  # morning|noon|evening
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """
        获取一条信息流内容

        策略：
          - 根据用户偏好选择内容类型
          - 随机选择一条内容
          - 记录推送
          - 如果今日首次 → 触发每日奖励
        """
        async with db or AsyncSessionLocal() as session:
            # 获取用户配置
            config = await self._get_config(session, user_id)
            if config and not config.feed_enabled:
                return {"skipped": True, "reason": "feed_disabled"}

            # 根据时段选择内容类型
            content_type = self._choose_content_type(time_slot, config)

            # 从种子库中选一条
            content_pool = SEED_CONTENT.get(content_type, SEED_CONTENT["news_brief"])
            content = random.choice(content_pool)

            # 记录信息流
            feed = DailyInfoFeed(
                user_id=user_id,
                source=content_type,
                original_text=content["text"],
                difficulty_level=content["difficulty"],
                vocab_extracted=content["vocab_hints"],
                user_interaction="pending",
            )
            session.add(feed)
            await session.commit()

            # 检查今日是否首次
            is_first_today = await self._is_first_feed_today(session, user_id)
            reward = None
            if is_first_today:
                from src.engine.reward_engine import RewardEngine
                reward = await RewardEngine().get_daily_reward(user_id)

            return {
                "feed_id": feed.id,
                "content_type": content_type,
                "text": content["text"],
                "difficulty": content["difficulty"],
                "vocab_hints": content["vocab_hints"],
                "source": content["source"],
                "is_first_today": is_first_today,
                "reward": reward,
            }

    async def get_morning_feed(self, user_id: str) -> dict:
        """获取晨间推送"""
        return await self.get_feed(user_id, "morning")

    async def get_noon_feed(self, user_id: str) -> dict:
        """获取午间推送"""
        return await self.get_feed(user_id, "noon")

    async def get_evening_feed(self, user_id: str) -> dict:
        """获取晚间推送"""
        return await self.get_feed(user_id, "evening")

    async def get_recent_feeds(self, user_id: str, limit: int = 10) -> list:
        """获取最近的信息流"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import desc
            stmt = select(DailyInfoFeed).where(
                DailyInfoFeed.user_id == user_id
            ).order_by(desc(DailyInfoFeed.created_at)).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": f.id,
                    "source": f.source,
                    "text": f.original_text[:100] + "..." if len(f.original_text) > 100 else f.original_text,
                    "difficulty": f.difficulty_level,
                    "interaction": f.user_interaction,
                    "comprehension_score": f.comprehension_score,
                    "created_at": f.created_at.isoformat(),
                }
                for f in result.scalars().all()
            ]

    async def update_comprehension(
        self,
        user_id: str,
        feed_id: str,
        score: float,
        duration_seconds: int,
    ) -> bool:
        """更新信息流的理解度评分"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(DailyInfoFeed).where(
                DailyInfoFeed.id == feed_id,
                DailyInfoFeed.user_id == user_id,
            )
            result = await session.execute(stmt)
            feed = result.scalar_one_or_none()
            if feed:
                feed.comprehension_score = score
                feed.duration_seconds = duration_seconds
                await session.commit()
                return True
            return False

    async def get_user_config(self, user_id: str) -> Optional[dict]:
        """获取用户配置"""
        async with AsyncSessionLocal() as session:
            config = await self._get_config(session, user_id)
            if not config:
                return None
            return {
                "trigger_time_slot": config.trigger_time_slot,
                "info_source_prefs": config.info_source_prefs,
                "action_prefs": config.action_prefs,
                "reward_frequency": config.reward_frequency,
                "feed_enabled": config.feed_enabled,
                "morning_time": config.morning_time,
                "noon_time": config.noon_time,
                "evening_time": config.evening_time,
            }

    async def update_user_config(self, user_id: str, updates: dict) -> dict:
        """更新用户配置"""
        async with AsyncSessionLocal() as session:
            config = await self._get_config(session, user_id)
            if not config:
                config = UserHabitConfig(user_id=user_id)
                session.add(config)

            allowed_fields = {
                "trigger_time_slot", "info_source_prefs", "action_prefs",
                "reward_frequency", "feed_enabled", "morning_time", "noon_time", "evening_time",
            }
            for k, v in updates.items():
                if k in allowed_fields:
                    setattr(config, k, v)

            await session.commit()
            return {"updated": list(updates.keys())}

    # ── 内部方法 ──

    async def _get_config(self, session: AsyncSession, user_id: str) -> Optional[UserHabitConfig]:
        stmt = select(UserHabitConfig).where(UserHabitConfig.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _choose_content_type(self, time_slot: str, config: Optional[UserHabitConfig] = None) -> str:
        """根据时段选择内容类型"""
        prefs = config.info_source_prefs if config and config.info_source_prefs else []
        if prefs:
            return random.choice(prefs)

        slot_map = {
            "morning": ["news_brief", "fun_fact"],
            "noon": ["social_post", "fun_fact"],
            "evening": ["vocab_card", "news_brief"],
        }
        pool = slot_map.get(time_slot, ["news_brief"])
        return random.choice(pool)

    async def _is_first_feed_today(self, session: AsyncSession, user_id: str) -> bool:
        """判断是否是今日首次推送"""
        today = date.today()
        stmt = select(func.count(DailyInfoFeed.id)).where(
            DailyInfoFeed.user_id == user_id,
            func.date(DailyInfoFeed.created_at) == today,
        )
        result = await session.execute(stmt)
        return result.scalar() <= 1