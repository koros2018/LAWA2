"""
Investment Engine — 投入引擎

§3.4 设计文档：
  用户投入越多，退出成本越高，形成习惯粘性
  - 语言资产：词汇收藏/句子摘录/日记历史/对话记录
  - 语言花园：词汇生命周期可视化（种子→发芽→幼苗→开花→结果）
  - 里程碑检测：自动检测并庆祝成长里程碑
"""
import uuid
from datetime import datetime, timezone, date
from typing import Optional
from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.habit import LanguageAsset, GrowthMilestone, MicroHabitLog, DailyInfoFeed
from src.models.user import User


# ── 词汇生命周期状态 ──

VOCAB_STAGES = {
    "seed": {"name": "种子", "emoji": "🌰", "icon": "seed"},
    "sprout": {"name": "发芽", "emoji": "🌱", "icon": "sprout"},
    "seedling": {"name": "幼苗", "emoji": "🌿", "icon": "seedling"},
    "bloom": {"name": "开花", "emoji": "🌼", "icon": "bloom"},
    "fruit": {"name": "结果", "emoji": "🍎", "icon": "fruit"},
}


# ── 里程碑模板 ──

MILESTONES = {
    "first_action": {
        "name": "第一步",
        "description": "完成了第一个微行为！语言花园开始生长。",
        "celebration_type": "confetti",
    },
    "first_10_words": {
        "name": "种子收集者",
        "description": "收藏了 10 个词汇，花园开始有了生机。",
        "celebration_type": "badge",
    },
    "first_100_words": {
        "name": "百词突破",
        "description": "语言花园拥有了 100 棵植物！",
        "celebration_type": "story",
    },
    "first_500_words": {
        "name": "小园丁",
        "description": "500 个词汇，你的花园已经初具规模。",
        "celebration_type": "confetti",
    },
    "3_day_streak": {
        "name": "三日园丁",
        "description": "连续 3 天照顾你的语言花园。",
        "celebration_type": "badge",
    },
    "7_day_streak": {
        "name": "一周园丁",
        "description": "连续 7 天！习惯正在形成。",
        "celebration_type": "story",
    },
    "30_day_streak": {
        "name": "月度园丁",
        "description": "坚持了整整一个月！语言花园已经枝繁叶茂。",
        "celebration_type": "confetti",
    },
    "first_native_post": {
        "name": "突破边界",
        "description": "第一次读懂了母语级别的英文内容。",
        "celebration_type": "story",
    },
    "first_bloom": {
        "name": "第一朵花",
        "description": "有一个词汇从'种子'开花了——你完全掌握了它！",
        "celebration_type": "confetti",
    },
    "level_5": {
        "name": "习惯大师",
        "description": "习惯等级达到 5 级。语言学习已经成为你的日常。",
        "celebration_type": "story",
    },
}


class InvestmentEngine:
    """投入引擎 — 语言资产沉淀与花园管理"""

    async def add_asset(
        self,
        user_id: str,
        asset_type: str,
        asset_data: dict,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """添加一条语言资产"""
        async with db or AsyncSessionLocal() as session:
            asset = LanguageAsset(
                user_id=user_id,
                asset_type=asset_type,
                asset_data=asset_data,
                word_count=len(str(asset_data).split()),
            )
            session.add(asset)
            await session.commit()

            return {
                "id": asset.id,
                "asset_type": asset_type,
                "word_count": asset.word_count,
            }

    async def get_assets(
        self,
        user_id: str,
        asset_type: Optional[str] = None,
        limit: int = 20,
    ) -> list:
        """获取用户的语言资产"""
        async with AsyncSessionLocal() as session:
            conditions = [LanguageAsset.user_id == user_id]
            if asset_type:
                conditions.append(LanguageAsset.asset_type == asset_type)

            stmt = select(LanguageAsset).where(
                and_(*conditions)
            ).order_by(LanguageAsset.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": a.id,
                    "type": a.asset_type,
                    "data": a.asset_data,
                    "word_count": a.word_count,
                    "created_at": a.created_at.isoformat(),
                }
                for a in result.scalars().all()
            ]

    async def get_garden_status(self, user_id: str) -> dict:
        """
        获取语言花园状态

        返回：
          - total_words: 总词汇数
          - by_stage: 各生命阶段数量
          - total_assets: 总资产数
          - recent_blooms: 最近开花
          - level: 习惯等级
        """
        async with AsyncSessionLocal() as session:
            # 总资产数
            stmt = select(func.count(LanguageAsset.id)).where(LanguageAsset.user_id == user_id)
            total_assets = (await session.execute(stmt)).scalar() or 0

            # 从 vocabulary_service 获取词汇状态（简化版，后续可扩展）
            vocab_count = await self._count_vocab(session, user_id)

            # 里程碑
            stmt = select(func.count(GrowthMilestone.id)).where(GrowthMilestone.user_id == user_id)
            milestone_count = (await session.execute(stmt)).scalar() or 0

            # 用户等级
            stmt = select(User).where(User.id == user_id)
            profile = (await session.execute(stmt)).scalar_one_or_none()

            # 如果用户不存在，自动创建
            if not profile:
                profile = User(id=user_id, username=user_id[:20])
                session.add(profile)
                await session.commit()

            streak = profile.streak_days or 0
            level = profile.habit_level or 1
            total_xp = profile.growth_xp or 0

            return {
                "total_vocab": vocab_count,
                "total_assets": total_assets,
                "total_milestones": milestone_count,
                "streak_days": streak,
                "habit_level": level,
                "total_xp": total_xp,
                "by_stage": {
                    "seed": max(0, vocab_count - 20) if vocab_count > 20 else vocab_count,
                    "sprout": min(vocab_count, max(0, vocab_count - 10)),
                    "seedling": min(5, vocab_count // 5),
                    "bloom": min(3, vocab_count // 20),
                    "fruit": min(1, vocab_count // 50),
                },
            }

    async def check_milestones(self, user_id: str) -> list:
        """
        检查并触发未解锁的里程碑

        返回：新解锁的里程碑列表
        """
        async with AsyncSessionLocal() as session:
            unlocked = set()
            stmt = select(GrowthMilestone).where(GrowthMilestone.user_id == user_id)
            existing = (await session.execute(stmt)).scalars().all()
            for m in existing:
                unlocked.add(m.milestone_code)

            new_milestones = []
            profile_stmt = select(User).where(User.id == user_id)
            profile = (await session.execute(profile_stmt)).scalar_one_or_none()
            if not profile:
                return []

            streak = profile.streak_days or 0
            level = profile.habit_level or 1

            # 检查各里程碑条件
            checks = [
                ("first_action", profile.growth_xp and profile.growth_xp > 0),
                ("3_day_streak", streak >= 3),
                ("7_day_streak", streak >= 7),
                ("30_day_streak", streak >= 30),
                ("level_5", level >= 5),
                ("first_bloom", await self._count_vocab(session, user_id) >= 20),
            ]

            for code, condition in checks:
                if code not in unlocked and condition:
                    tmpl = MILESTONES.get(code)
                    if tmpl:
                        milestone = GrowthMilestone(
                            user_id=user_id,
                            milestone_code=code,
                            milestone_name=tmpl["name"],
                            milestone_description=tmpl["description"],
                            celebration_type=tmpl["celebration_type"],
                        )
                        session.add(milestone)
                        new_milestones.append({
                            "code": code,
                            "name": tmpl["name"],
                            "description": tmpl["description"],
                            "celebration_type": tmpl["celebration_type"],
                        })

            if new_milestones:
                await session.commit()
                logger.info(f"用户 {user_id[:8]} 解锁了 {len(new_milestones)} 个新里程碑")

            return new_milestones

    async def get_milestones(self, user_id: str) -> list:
        """获取所有已解锁里程碑"""
        async with AsyncSessionLocal() as session:
            stmt = select(GrowthMilestone).where(
                GrowthMilestone.user_id == user_id
            ).order_by(GrowthMilestone.unlocked_at.desc())
            result = await session.execute(stmt)
            return [
                {
                    "code": m.milestone_code,
                    "name": m.milestone_name,
                    "description": m.milestone_description,
                    "unlocked_at": m.unlocked_at.isoformat(),
                    "celebration_type": m.celebration_type,
                }
                for m in result.scalars().all()
            ]

    # ── 内部方法 ──

    async def _count_vocab(self, session: AsyncSession, user_id: str) -> int:
        """统计词汇资产数量（简化版）"""
        stmt = select(func.count(LanguageAsset.id)).where(
            LanguageAsset.user_id == user_id,
            LanguageAsset.asset_type == "vocab_collection",
        )
        result = await session.execute(stmt)
        count = result.scalar() or 0

        # 从词汇服务中获取（后续可扩展）
        try:
            from src.services.vocabulary import VocabularyService
            svc = VocabularyService()
            vocab = await svc.get_user_vocabulary(user_id)
            count = max(count, len(vocab))
        except Exception:
            pass

        return count