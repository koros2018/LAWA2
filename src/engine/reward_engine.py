"""
Reward Engine — 可变奖励引擎

§3.3 设计文档：
  提供不可预测的可变奖励，保持用户好奇心
  - 打开就有"基础的"，但不知道"额外的"是什么
  - 模仿社交媒体刷新 → 下拉总有好东西

奖励类型：
  vocab_discovery           — 发现新词（中可变）
  comprehension_breakthrough — 理解突破（中可变）
  culture_egg               — 文化彩蛋（中可变）
  pattern_finding            — 兴趣模式发现（高可变）
  cross_language            — 跨语言发现（高可变）
  vocab_blossom             — 词汇开花（稀有）
"""
import uuid
import random
from datetime import datetime, timezone, date
from typing import Optional
from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.habit import (
    VariableReward, MicroHabitLog, DailyInfoFeed, GrowthMilestone,
)


# ── 奖励模板 ──

REWARD_TEMPLATES = {
    "vocab_discovery": {
        "name": "稀有词汇发现",
        "surprise_level": 3,
        "xp_bonus": 5,
        "icon": "🎉",
        "messages": [
            "你发现了一个稀有词汇 '{word}'！这个词在日常对话中不常见，但你遇到了它！",
            "🎊 隐藏词汇解锁！'{word}' 是今天的幸运词！",
            "咦，'{word}' 这个词可不简单——它在考试中出现的概率很高哦！",
        ],
    },
    "comprehension_breakthrough": {
        "name": "理解突破",
        "surprise_level": 3,
        "xp_bonus": 8,
        "icon": "💡",
        "messages": [
            "上周你还不太理解的 '{topic}' 主题，今天你已经能看懂 80% 了！",
            "你的理解力在悄悄成长——今天关于 '{topic}' 的内容读得比昨天流畅多了！",
            "进步可视化：'{topic}' 的理解度从 {old_score}% 提升到了 {new_score}%",
        ],
    },
    "culture_egg": {
        "name": "文化彩蛋",
        "surprise_level": 2,
        "xp_bonus": 3,
        "icon": "🥚",
        "messages": [
            "你知道吗？'{word}' 这个词来自一个有趣的文化背景……",
            "🍣 这个词在你的语言和英语中都有，但意思有点不一样哦！",
            "文化冷知识：{fact}",
        ],
    },
    "pattern_finding": {
        "name": "兴趣模式发现",
        "surprise_level": 4,
        "xp_bonus": 10,
        "icon": "🌱",
        "messages": [
            "我注意到你最近对 '{topic}' 很感兴趣！你已经积累了 {count} 个相关词汇。",
            "你的语言花园正在向 '{topic}' 方向生长——要看看这个主题的进阶内容吗？",
            "模式发现：你最近常读的 '{topic}' 内容，已经够看懂一篇完整文章了！",
        ],
    },
    "cross_language": {
        "name": "跨语言发现",
        "surprise_level": 4,
        "xp_bonus": 8,
        "icon": "🌍",
        "messages": [
            "'{word}' 这个词在 {lang} 里也有！你知道它们的联系吗？",
            "跨语言彩蛋：{word} → {translation}（{lang}）",
            "你的语言花园里有一棵'跨国植物'——'{word}' 在多种语言中都有！",
        ],
    },
    "vocab_blossom": {
        "name": "词汇开花",
        "surprise_level": 5,
        "xp_bonus": 20,
        "icon": "🌸",
        "messages": [
            "🌸 奇迹发生了！'{word}' 从'幼苗'开花了——你已经完全掌握了它！",
            "你的花园里有一朵花盛开了：'{word}' 已从'种子'成长为'开花'状态！",
            "恭喜！'{word}' 已经成为你的主动词汇——可以在真实场景中自如使用了！",
        ],
    },
}


class RewardEngine:
    """可变奖励引擎"""

    @staticmethod
    def get_reward_info(reward_type: str) -> Optional[dict]:
        return REWARD_TEMPLATES.get(reward_type)

    async def try_grant_reward(
        self,
        user_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[dict]:
        """
        尝试为用户发放可变奖励

        策略：
          - 每3个微行为 → 50% 概率触发中可变奖励
          - 每天第一次打开 → 必得一个中可变奖励（由 Trigger Engine 触发）
          - 连续7天 → 必得稀有奖励
          - 每周 → 一个高可变奖励

        返回：奖励详情 dict 或 None
        """
        async with db or AsyncSessionLocal() as session:
            # 1. 检查今天是否已给过稀有奖励（每天最多一次稀有）
            today = date.today()
            rare_count = await self._count_today_rewards(session, user_id, min_surprise=5)
            if rare_count >= 1:
                # 今天已有稀有奖励，只给中/低可变
                reward_type = random.choice(["vocab_discovery", "culture_egg"])
                return await self._grant(session, user_id, reward_type)

            # 2. 检查是否满足稀有奖励条件
            streak = await self._get_streak(session, user_id)
            if streak > 0 and streak % 7 == 0:
                # 连续7天的倍数 → 稀有奖励
                return await self._grant(session, user_id, "vocab_blossom")

            # 3. 随机选择奖励类型（带概率）
            roll = random.random()
            if roll < 0.1:  # 10% 高可变
                reward_type = random.choice(["pattern_finding", "cross_language"])
            elif roll < 0.5:  # 40% 中可变
                reward_type = random.choice(["vocab_discovery", "comprehension_breakthrough", "culture_egg"])
            else:
                return None  # 50% 无奖励（保持不可预测性）

            return await self._grant(session, user_id, reward_type)

    async def get_daily_reward(self, user_id: str) -> Optional[dict]:
        """
        每日首次打开必得奖励

        由 Trigger Engine 在每日首次推送时调用
        """
        async with AsyncSessionLocal() as session:
            today = date.today()
            # 检查今天是否已领取过每日奖励
            stmt = select(func.count(VariableReward.id)).where(
                VariableReward.user_id == user_id,
                func.date(VariableReward.created_at) == today,
                VariableReward.reward_type.in_(["vocab_discovery", "culture_egg"]),
            )
            result = await session.execute(stmt)
            if result.scalar() > 0:
                return None  # 今天已领过

            # 给一个中可变奖励
            reward_type = random.choice(["vocab_discovery", "culture_egg"])
            return await self._grant(session, user_id, reward_type)

    async def get_recent_rewards(self, user_id: str, limit: int = 10) -> list:
        """获取最近的奖励记录"""
        async with AsyncSessionLocal() as session:
            stmt = select(VariableReward).where(
                VariableReward.user_id == user_id
            ).order_by(VariableReward.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": r.id,
                    "reward_type": r.reward_type,
                    "reward_value": r.reward_value,
                    "surprise_level": r.surprise_level,
                    "xp_bonus": r.xp_bonus,
                    "created_at": r.created_at.isoformat(),
                }
                for r in result.scalars().all()
            ]

    # ── 内部方法 ──

    async def _grant(self, session: AsyncSession, user_id: str, reward_type: str) -> dict:
        """发放奖励"""
        template = REWARD_TEMPLATES.get(reward_type)
        if not template:
            logger.warning(f"未知奖励类型: {reward_type}")
            return None

        # 生成奖励详情
        reward_value = {
            "type": reward_type,
            "name": template["name"],
            "icon": template["icon"],
            "message": random.choice(template["messages"]),
        }

        # 创建记录
        reward = VariableReward(
            user_id=user_id,
            reward_type=reward_type,
            reward_value=reward_value,
            surprise_level=template["surprise_level"],
            xp_bonus=template["xp_bonus"],
        )
        session.add(reward)

        # 给用户加 XP（使用 get_or_create 避免并发冲突）
        from src.models.user import User
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.exc import IntegrityError
        
        # 先尝试查询用户
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            # 用户不存在，尝试创建（使用重试机制处理并发冲突）
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # 直接插入，不指定 ON CONFLICT
                    # 如果另一个请求先创建了用户，会因 id 或 username 唯一约束失败
                    stmt = sqlite_insert(User).values(
                        id=user_id,
                        username=user_id[:20],
                        native_lang="zh",
                        learn_lang="en",
                        interests="[]",
                        growth_xp=0,
                        habit_level=1,
                        streak_days=0,
                        bridge_level=0,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        is_active=True,
                        is_admin=False,
                    )
                    await session.execute(stmt)
                    
                    # 重新查询用户
                    stmt = select(User).where(User.id == user_id)
                    result = await session.execute(stmt)
                    profile = result.scalar_one_or_none()
                    if not profile:
                        raise ValueError(f"User {user_id} not found after insert")
                    break
                    
                except IntegrityError as e:
                    # 并发创建失败（id 或 username 冲突），回滚并重试
                    await session.rollback()
                    if attempt < max_retries - 1:
                        # 短暂等待后重试
                        import asyncio
                        await asyncio.sleep(0.01 * (attempt + 1))
                        # 重新查询用户（可能在其他请求中已创建）
                        stmt = select(User).where(User.id == user_id)
                        result = await session.execute(stmt)
                        profile = result.scalar_one_or_none()
                        if profile:
                            break
                        continue
                    else:
                        # 最后一次尝试，使用新 session 查询
                        async with AsyncSessionLocal() as new_session:
                            stmt = select(User).where(User.id == user_id)
                            result = await new_session.execute(stmt)
                            profile = result.scalar_one_or_none()
                            if not profile:
                                raise
                            # 获取用户 XP 并更新
                            current_xp = profile.growth_xp or 0
                            new_xp = current_xp + template["xp_bonus"]
                            profile.growth_xp = new_xp
                            await new_session.commit()
                        # 使用新 session 创建 reward
                        async with AsyncSessionLocal() as reward_session:
                            new_reward = VariableReward(
                                user_id=user_id,
                                reward_type=reward_type,
                                reward_value=reward_value,
                                surprise_level=template["surprise_level"],
                                xp_bonus=template["xp_bonus"],
                            )
                            reward_session.add(new_reward)
                            await reward_session.commit()
                        logger.info(f"奖励 {reward_type} 发放给用户 {user_id[:8]}, +{template['xp_bonus']}xp (并发创建重试)")
                        return {
                            "id": new_reward.id,
                            "reward_type": reward_type,
                            "reward_value": reward_value,
                            "surprise_level": template["surprise_level"],
                            "xp_bonus": template["xp_bonus"],
                        }
        
        # 更新 XP
        profile.growth_xp = (profile.growth_xp or 0) + template["xp_bonus"]

        await session.commit()

        logger.info(f"奖励 {reward_type} 发放给用户 {user_id[:8]}, +{template['xp_bonus']}xp")

        return {
            "id": reward.id,
            "reward_type": reward_type,
            "reward_value": reward_value,
            "surprise_level": template["surprise_level"],
            "xp_bonus": template["xp_bonus"],
        }

    async def _count_today_rewards(self, session: AsyncSession, user_id: str, min_surprise: int = 1) -> int:
        """统计今日奖励数"""
        today = date.today()
        stmt = select(func.count(VariableReward.id)).where(
            VariableReward.user_id == user_id,
            func.date(VariableReward.created_at) == today,
            VariableReward.surprise_level >= min_surprise,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def _get_streak(self, session: AsyncSession, user_id: str) -> int:
        from src.models.user import User
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        return profile.streak_days or 0