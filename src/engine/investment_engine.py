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
from src.models.habit import LanguageAsset, GrowthMilestone, MicroHabitLog, DailyInfoFeed, SocialVocab, SocialSceneLog
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
                import uuid as _uuid
                _new_id = str(_uuid.uuid4())
                _username = user_id[:20] if user_id != 'default_user' else 'garden_user'
                profile = User(id=_new_id, username=_username)
                try:
                    session.add(profile)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    profile = User(id=_new_id, username=f"{_username[:16]}_{_uuid.uuid4().hex[:8]}")
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

    async def get_vocab_details(self, user_id: str) -> dict:
        """
        获取词汇明细（含社交词汇）

        返回:
          - social_words: 社交词汇列表
          - by_category: 按社交分类统计
          - total: 总词汇数
          - stage_vocab: 按花园阶段分组
        """
        async with AsyncSessionLocal() as session:
            # 社交词汇
            stmt = select(SocialVocab).where(SocialVocab.user_id == user_id).order_by(SocialVocab.learned_at.desc())
            result = await session.execute(stmt)
            social_words = []
            cat_count: dict = {}
            for sv in result.scalars().all():
                cat = sv.category or "other"
                cat_count[cat] = cat_count.get(cat, 0) + 1
                social_words.append({
                    "id": sv.id,
                    "word": sv.word,
                    "meaning": sv.meaning,
                    "category": sv.category,
                    "understanding_level": sv.understanding_level,
                    "lang_direction": sv.lang_direction,
                    "created_at": sv.learned_at.isoformat() if sv.learned_at else None,
                })

            # 按理解度分级（花园阶段映射）
            stage_map = {
                "seed": [],       # 新收录
                "sprout": [],     # 能看懂
                "seedling": [],   # 能使用
                "bloom": [],      # 能创作
                "fruit": [],      # 精通（能教别人）
            }
            for sv in social_words:
                lvl = sv.get("understanding_level", "understand")
                if lvl == "understand":
                    stage_map["sprout"].append(sv)
                elif lvl == "use":
                    stage_map["seedling"].append(sv)
                elif lvl == "create":
                    stage_map["bloom"].append(sv)
                else:
                    stage_map["seed"].append(sv)

            # 总词汇（含已有资产）
            total_vocab = len(social_words)
            try:
                from src.services.vocabulary import VocabularyService
                svc = VocabularyService()
                vocab = await svc.get_user_vocabulary(user_id)
                total_vocab = max(total_vocab, len(vocab))
            except Exception:
                pass

            return {
                "social_words": social_words,
                "by_category": cat_count,
                "total": total_vocab,
                "stage_vocab": {k: [v["word"] for v in vs] for k, vs in stage_map.items()},
                "stage_count": {k: len(vs) for k, vs in stage_map.items()},
            }

    async def get_growth_curve(self, user_id: str) -> dict:
        """
        获取成长曲线数据（近7/30天）

        返回:
          - daily_actions: 每日习惯记录数
          - daily_vocab: 每日新增词汇
          - streak_history: 连续天数
        """
        from datetime import timedelta
        async with AsyncSessionLocal() as session:
            today = date.today()
            week_ago = today - timedelta(days=6)
            month_ago = today - timedelta(days=29)

            # 每日习惯记录
            stmt = select(
                func.date(MicroHabitLog.created_at).label("day"),
                func.count(MicroHabitLog.id).label("count"),
            ).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(month_ago.isoformat()),
            ).group_by(func.date(MicroHabitLog.created_at)).order_by("day")
            result = await session.execute(stmt)
            daily_actions = {row.day: row.count for row in result.all()}

            # 每日社交词汇
            stmt = select(
                func.date(SocialVocab.learned_at).label("day"),
                func.count(SocialVocab.id).label("count"),
            ).where(
                SocialVocab.user_id == user_id,
                SocialVocab.learned_at >= func.datetime(month_ago.isoformat()),
            ).group_by(func.date(SocialVocab.learned_at)).order_by("day")
            result = await session.execute(stmt)
            daily_vocab = {row.day: row.count for row in result.all()}

            # 组装 30 天序列
            days_30 = [(month_ago + timedelta(days=i)).isoformat() for i in range(30)]

            return {
                "actions_30d": [daily_actions.get(d, 0) for d in days_30],
                "vocab_30d": [daily_vocab.get(d, 0) for d in days_30],
                "days_30": days_30,
                "total_actions_7d": sum(daily_actions.get(d, 0) for d in [(today - timedelta(days=i)).isoformat() for i in range(7)]),
                "total_vocab_7d": sum(daily_vocab.get(d, 0) for d in [(today - timedelta(days=i)).isoformat() for i in range(7)]),
            }

    async def get_garden_report(self, user_id: str) -> dict:
        """
        花园周报 — 生成叙事化的花园状态报告

        返回:
          - report: 文本报告（中英双轨自适应）
          - highlights: 本周亮点列表
          - can_water: 是否可以浇水（每日首次获得积分加成的习惯行为）
          - watered_today: 是否已浇水
        """
        from datetime import timedelta
        async with AsyncSessionLocal() as session:
            today = date.today()
            week_ago = today - timedelta(days=6)

            # 本周习惯记录数
            stmt = select(func.count(MicroHabitLog.id)).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(week_ago.isoformat()),
            )
            week_actions = (await session.execute(stmt)).scalar() or 0

            # 本周新增词汇
            stmt = select(func.count(SocialVocab.id)).where(
                SocialVocab.user_id == user_id,
                SocialVocab.learned_at >= func.datetime(week_ago.isoformat()),
            )
            week_vocab = (await session.execute(stmt)).scalar() or 0

            # 今天是否已浇水（有习惯记录）
            stmt = select(func.count(MicroHabitLog.id)).where(
                MicroHabitLog.user_id == user_id,
                func.date(MicroHabitLog.created_at) == today.isoformat(),
            )
            today_actions = (await session.execute(stmt)).scalar() or 0

            # 用户等级
            profile_stmt = select(User).where(User.id == user_id)
            profile = (await session.execute(profile_stmt)).scalar_one_or_none()
            level = profile.habit_level if profile else 1
            streak = profile.streak_days if profile else 0
            total_xp = profile.growth_xp if profile else 0

            # 获取语言方向
            lang_dir = profile.learn_lang if profile else "en"

            # 生成周报叙事
            if lang_dir == "en":
                report_segments = [
                    f"Your language garden has **{level}** plants this week.",
                    f"You performed **{week_actions}** micro-habits and added **{week_vocab}** new words.",
                    f"Current streak: **{streak}** days — keep it growing!",
                ]
            else:
                report_segments = [
                    f"你的语言花园本周有 **{level}** 棵植物在生长。",
                    f"你完成了 **{week_actions}** 个微行为，学习了 **{week_vocab}** 个新词。",
                    f"当前连续 **{streak}** 天 — 保持下去！",
                ]

            # 亮点检测
            highlights = []
            if week_actions >= 14:
                highlights.append("daily_habit_streak" if lang_dir == "en" else "每日习惯连续")
            if week_vocab >= 5:
                highlights.append("vocab_explosion" if lang_dir == "en" else "词汇爆发期")
            if streak >= 7:
                highlights.append("full_week_streak" if lang_dir == "en" else "满一周坚持")

            return {
                "report": "\n\n".join(report_segments),
                "highlights": highlights,
                "week_actions": week_actions,
                "week_vocab": week_vocab,
                "total_xp": total_xp,
                "level": level,
                "streak": streak,
                "can_water": today_actions == 0,
                "watered_today": today_actions > 0,
                "lang_direction": lang_dir,
            }

    async def get_health_insights(self, user_id: str) -> dict:
        """
        获取习惯健康度洞察

        返回:
          - health_score: 0-100 综合健康度
          - trend: "up" | "down" | "stable"
          - dimensions: {
              consistency: 持续度
              depth: 深入度
              breadth: 广度
              recovery: 恢复力
            }
          - recommendation: 下一步建议
        """
        from datetime import timedelta
        async with AsyncSessionLocal() as session:
            today = date.today()
            week_ago = today - timedelta(days=6)
            month_ago = today - timedelta(days=29)

            profile_stmt = select(User).where(User.id == user_id)
            profile = (await session.execute(profile_stmt)).scalar_one_or_none()
            if not profile:
                return {"health_score": 0, "trend": "stable", "dimensions": {}, "recommendation": ""}

            lang_dir = profile.learn_lang or "en"

            # 1. 持续度 consistency — 过去 7 天有多少天有微行为
            stmt = select(func.date(MicroHabitLog.created_at).label("day")).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(week_ago.isoformat()),
            ).distinct()
            result = await session.execute(stmt)
            active_days = len(result.all())
            consistency = min(100, (active_days / 7) * 100)

            # 2. 深入度 depth — 每打开平均行为数
            stmt = select(func.count(MicroHabitLog.id)).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(week_ago.isoformat()),
            )
            total_actions = (await session.execute(stmt)).scalar() or 0
            depth = min(100, (total_actions / max(active_days, 1)) * 20)

            # 3. 广度 breadth — 覆盖的行为类型数
            stmt = select(MicroHabitLog.habit_code).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(week_ago.isoformat()),
            ).distinct()
            result = await session.execute(stmt)
            distinct_types = len(result.all())
            breadth = min(100, distinct_types * 25)

            # 4. 恢复力 recovery — 连续天数 / 7
            streak = profile.streak_days or 0
            recovery = min(100, (streak / 7) * 100)

            health_score = round((consistency * 0.30 + depth * 0.25 + breadth * 0.25 + recovery * 0.20))

            # 趋势判断
            month_stmt = select(func.count(MicroHabitLog.id)).where(
                MicroHabitLog.user_id == user_id,
                MicroHabitLog.created_at >= func.datetime(month_ago.isoformat()),
                MicroHabitLog.created_at < func.datetime(week_ago.isoformat()),
            )
            prev_month_actions = (await session.execute(month_stmt)).scalar() or 0
            if total_actions > prev_month_actions * 1.2:
                trend = "up"
            elif total_actions < prev_month_actions * 0.8:
                trend = "down"
            else:
                trend = "stable"

            # 推荐
            if health_score < 30:
                recommendation = {
                    "en": "Try to open LAWA2 at least once a day — even 30 seconds counts.",
                    "zh": "尝试每天至少打开一次 LAWA2，哪怕只有 30 秒。",
                }.get(lang_dir, "")
            elif health_score < 60:
                recommendation = {
                    "en": "Great start! Try to cover more habit types like reading AND listening.",
                    "zh": "好的开始！尝试覆盖更多行为类型，比如读和听都做。",
                }.get(lang_dir, "")
            elif health_score < 85:
                recommendation = {
                    "en": "You're building real momentum! Consistency is your superpower.",
                    "zh": "势头不错！持续是你最大的超能力。",
                }.get(lang_dir, "")
            else:
                recommendation = {
                    "en": "Amazing! Your language garden is thriving. Try connecting with a bridge partner next.",
                    "zh": "太棒了！你的语言花园欣欣向荣。试试开启桥梁语伴吧。",
                }.get(lang_dir, "")

            return {
                "health_score": health_score,
                "trend": trend,
                "dimensions": {
                    "consistency": round(consistency),
                    "depth": round(depth),
                    "breadth": round(breadth),
                    "recovery": round(recovery),
                },
                "recommendation": recommendation,
            }

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