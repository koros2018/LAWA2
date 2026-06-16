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


def _utcnow():
    return datetime.now(timezone.utc)


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


# ── 社交场景种子语料库 ──

SOCIAL_SCENE_SEED = {
    "net_slang": {
        # 英文母语者学中文（Alice方向）
        "zh": [
            {
                "word": "破防了",
                "meaning": "被戳中笑点/泪点/槽点，忍不住了",
                "scene_example": "A: 这张猫的照片太搞笑了 B: 哈哈哈哈破防了",
                "difficulty": "medium",
            },
            {
                "word": "绝绝子",
                "meaning": "太绝了、太好了（夸张用法）",
                "scene_example": "A: 这家火锅太好吃了！ B: 绝绝子！",
                "difficulty": "medium",
            },
            {
                "word": "栓Q",
                "meaning": "感谢的搞笑说法（来自'Thank you'的谐音）",
                "scene_example": "朋友帮你带了奶茶 → 回复：'栓Q栓Q'",
                "difficulty": "easy",
            },
            {
                "word": "YYDS",
                "meaning": "永远的神（eternal god）——形容某人/物极其优秀",
                "scene_example": "看完这部电影 → 发朋友圈：'YYDS！'",
                "difficulty": "easy",
            },
            {
                "word": "6",
                "meaning": "形容操作厉害/流畅（来自游戏术语）",
                "scene_example": "看到朋友的操作 → 回复一个'6'",
                "difficulty": "easy",
            },
        ],
        # 中文母语者学英文（Bob方向）
        "en": [
            {
                "word": "iykyk",
                "meaning": "if you know, you know — only insiders get it",
                "scene_example": "Posting an inside joke: 'iykyk'",
                "difficulty": "medium",
            },
            {
                "word": "no cap",
                "meaning": "no lie / for real — emphasizing truthfulness",
                "scene_example": "A: This pizza is amazing B: No cap, best I've had",
                "difficulty": "medium",
            },
            {
                "word": "that's what she said",
                "meaning": "a classic innuendo joke, used after an accidentally suggestive sentence",
                "scene_example": "A: 'It's too big to fit' B: 'That's what she said!' (everyone laughs)",
                "difficulty": "hard",
            },
            {
                "word": "fr fr",
                "meaning": "for real for real — seriously / genuinely",
                "scene_example": "A: I actually loved that movie B: Fr fr? I thought it was mid",
                "difficulty": "easy",
            },
            {
                "word": "I'm dead",
                "meaning": "something is so funny I 'died' of laughter",
                "scene_example": "After a hilarious joke: 'I'm dead 💀'",
                "difficulty": "easy",
            },
        ],
    },
    "life_scene": {
        "zh": [
            {
                "word": "多点辣",
                "meaning": "点餐时要求加辣",
                "scene_example": "面摊老板问辣度 → 说'多点辣'",
                "difficulty": "easy",
            },
            {
                "word": "打包",
                "meaning": "把剩下的食物带走",
                "scene_example": "吃不完 → 跟服务员说'打包'",
                "difficulty": "easy",
            },
            {
                "word": "鸳鸯锅",
                "meaning": "一半辣一半不辣的火锅锅底",
                "scene_example": "点火锅 → '我要一个鸳鸯锅'",
                "difficulty": "easy",
            },
            {
                "word": "不好意思",
                "meaning": "万能道歉/打扰语（比'对不起'更日常）",
                "scene_example": "不小心碰到人 → '不好意思' / 问路前 → '不好意思请问'",
                "difficulty": "easy",
            },
        ],
        "en": [
            {
                "word": "You alright?",
                "meaning": "British greeting — not asking if you're ok, just saying hi",
                "scene_example": "Walking into a pub: bartender says 'You alright?' → reply 'Yeah, pint please'",
                "difficulty": "medium",
            },
            {
                "word": "Cheers mate",
                "meaning": "Multi-purpose: thanks / goodbye / toast (UK/Australia)",
                "scene_example": "Barista hands you coffee → 'Cheers mate'",
                "difficulty": "easy",
            },
            {
                "word": "Can I get the bill?",
                "meaning": "'Check please' in UK/AU restaurants",
                "scene_example": "Finished eating → catch waiter's eye → 'Can I get the bill please?'",
                "difficulty": "easy",
            },
            {
                "word": "My bad",
                "meaning": "casual apology, less serious than 'sorry'",
                "scene_example": "Accidentally bump into someone → 'Oh my bad'",
                "difficulty": "easy",
            },
        ],
    },
    "group_chat": {
        "zh": [
            {
                "word": "哈哈哈哈笑死",
                "meaning": "看到好笑内容的典型回复",
                "scene_example": "群里有人发搞笑视频 → 回复'哈哈哈哈笑死'",
                "difficulty": "easy",
            },
            {
                "word": "我也是",
                "meaning": "表示赞同/共鸣",
                "scene_example": "A说'这电影太好哭了' → B回复'我也是！'",
                "difficulty": "easy",
            },
            {
                "word": "真的吗？",
                "meaning": "惊讶/好奇时的回复",
                "scene_example": "A说'我昨天中了奖' → B回复'真的吗？？'",
                "difficulty": "easy",
            },
        ],
        "en": [
            {
                "word": "Same lol",
                "meaning": "agreeing + laughing about it",
                "scene_example": "A: 'I haven't done my laundry in 2 weeks' B: 'Same lol'",
                "difficulty": "easy",
            },
            {
                "word": "wdym?",
                "meaning": "what do you mean? — asking for clarification",
                "scene_example": "A: 'It's giving main character energy' B: 'Wdym?'",
                "difficulty": "medium",
            },
            {
                "word": "No way!",
                "meaning": "shocked/disbelieving reaction",
                "scene_example": "A: 'I met Taylor Swift yesterday' B: 'No way!'",
                "difficulty": "easy",
            },
        ],
    },
    "meme": {
        "zh": [
            {
                "word": "啊对对对",
                "meaning": "敷衍/嘲讽式同意（配翻白眼表情）",
                "scene_example": "有人抬杠 → 回复'啊对对对你说得都对'",
                "difficulty": "hard",
            },
            {
                "word": "我哭死",
                "meaning": "夸张表达感动/好笑",
                "scene_example": "朋友帮你做了件小事 → '我哭死😭'",
                "difficulty": "medium",
            },
        ],
        "en": [
            {
                "word": "I am once again asking...",
                "meaning": "Bernie Sanders meme — humorously asking for something again",
                "scene_example": "'I am once again asking for someone to bring snacks to the meeting'",
                "difficulty": "hard",
            },
            {
                "word": "It's giving ____",
                "meaning": "meme format — something gives off a certain vibe",
                "scene_example": "'That outfit is giving main character energy'",
                "difficulty": "hard",
            },
        ],
    },
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

    # ── 社交场景方法 ──

    async def get_social_scene(
        self,
        user_id: str,
        lang_direction: str = "zh",  # zh=学中文, en=学英文
        category: str = "net_slang",  # net_slang|life_scene|group_chat|meme
    ) -> dict:
        """获取一条社交场景内容"""
        pool = SOCIAL_SCENE_SEED.get(category, SOCIAL_SCENE_SEED["net_slang"])
        lang_pool = pool.get(lang_direction, pool["zh"])
        item = random.choice(lang_pool)

        async with AsyncSessionLocal() as session:
            # 记录到 social_vocab
            from src.models.habit import SocialVocab, SocialSceneLog

            vocab = SocialVocab(
                user_id=user_id,
                word=item["word"],
                meaning=item["meaning"],
                scene_example=item["scene_example"],
                category=category,
                understanding_level="understand",
            )
            session.add(vocab)
            await session.commit()

            return {
                "vocab_id": vocab.id,
                "word": item["word"],
                "meaning": item["meaning"],
                "scene_example": item["scene_example"],
                "difficulty": item["difficulty"],
                "category": category,
                "lang_direction": lang_direction,
                "understanding_level": "understand",
            }

    async def get_social_scene_by_level(
        self,
        user_id: str,
        lang_direction: str = "zh",
    ) -> dict:
        """根据用户社交理解度推送合适场景"""
        # 用户所有已学社交词汇
        async with AsyncSessionLocal() as session:
            from src.models.habit import SocialVocab, SocialSceneLog
            from sqlalchemy import desc, func as sa_func

            # 已掌握各等级的词汇数
            stmt = select(
                SocialVocab.understanding_level,
                sa_func.count(SocialVocab.id),
            ).where(SocialVocab.user_id == user_id).group_by(SocialVocab.understanding_level)
            result = await session.execute(stmt)
            levels = {row[0]: row[1] for row in result}

            understand_count = levels.get("understand", 0)
            use_count = levels.get("use", 0)
            cat_pool = ["net_slang", "life_scene", "group_chat", "meme"]

            # 如果已经有很多词汇，推 harder 类型
            if use_count > 5:
                weights = {"net_slang": 0.2, "life_scene": 0.2, "group_chat": 0.3, "meme": 0.3}
            elif understand_count > 10:
                weights = {"net_slang": 0.3, "life_scene": 0.25, "group_chat": 0.25, "meme": 0.2}
            else:
                weights = {"net_slang": 0.3, "life_scene": 0.4, "group_chat": 0.2, "meme": 0.1}

            # 加权随机选择
            cats = list(weights.keys())
            w = [weights[c] for c in cats]
            category = random.choices(cats, weights=w, k=1)[0]

        return await self.get_social_scene(user_id, lang_direction, category)

    async def update_social_understanding(
        self,
        user_id: str,
        vocab_id: str,
        new_level: str,  # understand|use|create
    ) -> bool:
        """更新社交词汇的理解等级"""
        async with AsyncSessionLocal() as session:
            from src.models.habit import SocialVocab
            from sqlalchemy import select
            stmt = select(SocialVocab).where(
                SocialVocab.id == vocab_id,
                SocialVocab.user_id == user_id,
            )
            result = await session.execute(stmt)
            v = result.scalar_one_or_none()
            if not v:
                return False
            v.understanding_level = new_level
            v.last_reviewed = _utcnow()
            v.review_count = v.review_count + 1 if v.review_count else 1
            await session.commit()
            return True

    async def get_social_progress(self, user_id: str) -> dict:
        """获取社交学习进度"""
        async with AsyncSessionLocal() as session:
            from src.models.habit import SocialVocab
            from sqlalchemy import select, func as sa_func

            stmt = select(
                SocialVocab.category,
                SocialVocab.understanding_level,
                sa_func.count(SocialVocab.id),
            ).where(SocialVocab.user_id == user_id).group_by(
                SocialVocab.category, SocialVocab.understanding_level
            )
            result = await session.execute(stmt)

            # 构建分类统计
            categories = ["net_slang", "life_scene", "group_chat", "meme"]
            progress = {}
            total_understand = 0
            total_use = 0
            for cat in categories:
                progress[cat] = {"understand": 0, "use": 0, "create": 0}

            for row in result:
                cat = row[0]
                level = row[1]
                count = row[2]
                if cat in progress:
                    progress[cat][level] = count
                    if level == "understand":
                        total_understand += count
                    elif level == "use":
                        total_use += count

            return {
                "by_category": progress,
                "total_understand": total_understand,
                "total_use": total_use,
                "total_all": total_understand + total_use,
            }

    async def _is_first_feed_today(self, session: AsyncSession, user_id: str) -> bool:
        """判断是否是今日首次推送"""
        today = date.today()
        stmt = select(func.count(DailyInfoFeed.id)).where(
            DailyInfoFeed.user_id == user_id,
            func.date(DailyInfoFeed.created_at) == today,
        )
        result = await session.execute(stmt)
        return result.scalar() <= 1