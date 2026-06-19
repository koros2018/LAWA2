"""
LAWA 词汇卡片服务

- WordCard CRUD（独立于 companion 系统的通用词汇卡片）
- SM-2 间隔复习调度
- 从 companion 生词本同步
- 复习队列 + 统计
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.word_card import WordCard, WordCardReview


class WordCardService:
    """词汇卡片服务"""

    def __init__(self):
        self.logger = logger.bind(service="word_card")

    async def create_card(
        self,
        db: AsyncSession,
        user_id: str,
        word: str,
        lang: str = "en",
        definition: Optional[str] = None,
        definition_native: Optional[str] = None,
        part_of_speech: Optional[str] = None,
        phonetic: Optional[str] = None,
        example_sentence: Optional[str] = None,
        example_translation: Optional[str] = None,
        source: str = "manual",
        source_id: Optional[str] = None,
        tags: Optional[list] = None,
        difficulty: int = 3,
    ) -> dict:
        """创建一张词汇卡片（自动去重）"""
        # 去重检查
        exist = await db.execute(
            select(WordCard).where(
                WordCard.user_id == user_id,
                WordCard.word == word,
                WordCard.lang == lang,
            )
        )
        existing = exist.scalar_one_or_none()
        if existing:
            # 更新已有卡片的信息
            if definition:
                existing.definition = definition
            if example_sentence:
                existing.example_sentence = example_sentence
            if part_of_speech:
                existing.part_of_speech = part_of_speech
            await db.commit()
            self.logger.info(f"词汇卡片已存在，更新: {word}")
            return self._to_dict(existing)

        card = WordCard(
            user_id=user_id,
            word=word.strip(),
            lang=lang,
            definition=definition,
            definition_native=definition_native,
            part_of_speech=part_of_speech,
            phonetic=phonetic,
            example_sentence=example_sentence,
            example_translation=example_translation,
            source=source,
            source_id=source_id,
            tags=json.dumps(tags or [], ensure_ascii=False),
            difficulty=difficulty,
            # SM-2 初始调度
            review_interval_hours=0,
            ease_factor=2.5,
            next_review_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)
        self.logger.info(f"创建词汇卡片: {word} (user={user_id}, lang={lang})")
        return self._to_dict(card)

    async def get_card(self, db: AsyncSession, card_id: str) -> Optional[dict]:
        """获取单张卡片"""
        try:
            cid = uuid.UUID(card_id)
        except ValueError:
            return None
        result = await db.execute(select(WordCard).where(WordCard.id == cid))
        card = result.scalar_one_or_none()
        return self._to_dict(card) if card else None

    async def list_cards(
        self,
        db: AsyncSession,
        user_id: str,
        lang: str = "en",
        mastered: Optional[bool] = None,
        favorited: Optional[bool] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取卡片列表（分页）"""
        conditions = [WordCard.user_id == user_id, WordCard.lang == lang]
        if mastered is not None:
            conditions.append(WordCard.is_mastered == mastered)
        if favorited is not None:
            conditions.append(WordCard.is_favorited == favorited)
        if source:
            conditions.append(WordCard.source == source)
        if search:
            conditions.append(WordCard.word.ilike(f"%{search}%"))

        # 总数
        count_result = await db.execute(select(func.count(WordCard.id)).where(and_(*conditions)))
        total = count_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(
            select(WordCard)
            .where(and_(*conditions))
            .order_by(WordCard.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        cards = result.scalars().all()

        return {
            "items": [self._to_dict(c) for c in cards],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def update_card(self, db: AsyncSession, card_id: str, update_data: dict) -> Optional[dict]:
        """更新卡片字段"""
        try:
            cid = uuid.UUID(card_id)
        except ValueError:
            return None

        result = await db.execute(select(WordCard).where(WordCard.id == cid))
        card = result.scalar_one_or_none()
        if not card:
            return None

        for key, value in update_data.items():
            if key == "tags" and isinstance(value, list):
                setattr(card, key, json.dumps(value, ensure_ascii=False))
            else:
                setattr(card, key, value)

        await db.commit()
        await db.refresh(card)
        return self._to_dict(card)

    async def delete_card(self, db: AsyncSession, card_id: str) -> bool:
        """删除卡片"""
        try:
            cid = uuid.UUID(card_id)
        except ValueError:
            return False

        result = await db.execute(select(WordCard).where(WordCard.id == cid))
        card = result.scalar_one_or_none()
        if not card:
            return False

        await db.delete(card)
        await db.commit()
        return True

    async def review_card(self, db: AsyncSession, card_id: str, user_id: str, quality: int) -> dict:
        """提交复习，更新 SM-2 调度"""
        try:
            cid = uuid.UUID(card_id)
        except ValueError:
            return {"error": "Invalid card id"}

        result = await db.execute(select(WordCard).where(WordCard.id == cid))
        card = result.scalar_one_or_none()
        if not card:
            return {"error": "Card not found"}

        # SM-2 计算
        next_interval, new_ease, new_count, mastered = self._schedule_next_review(
            current_interval=card.review_interval_hours,
            ease_factor=card.ease_factor,
            quality=quality,
            review_count=card.review_count,
        )

        card.review_count = new_count
        card.review_interval_hours = next_interval
        card.ease_factor = new_ease
        card.last_review_at = datetime.now(timezone.utc)
        card.next_review_at = datetime.now(timezone.utc) + timedelta(hours=next_interval)
        card.is_mastered = mastered

        # 记录复习日志
        review_log = WordCardReview(
            card_id=cid,
            user_id=user_id,
            quality=quality,
        )
        db.add(review_log)
        await db.commit()

        self.logger.info(f"复习: {card.word} | q={quality} → interval={next_interval:.1f}h mastered={mastered}")

        return {
            "id": str(card.id),
            "word": card.word,
            "quality": quality,
            "next_interval_hours": round(next_interval, 1),
            "next_review_at": card.next_review_at.isoformat() if card.next_review_at else None,
            "is_mastered": mastered,
            "review_count": new_count,
        }

    async def get_review_queue(self, db: AsyncSession, user_id: str, lang: str = "en", limit: int = 20) -> list:
        """获取待复习队列"""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(WordCard)
            .where(
                WordCard.user_id == user_id,
                WordCard.lang == lang,
                WordCard.is_mastered == False,
                WordCard.next_review_at <= now,
            )
            .order_by(WordCard.next_review_at.asc())
            .limit(limit)
        )
        cards = result.scalars().all()

        queue = []
        for card in cards:
            overdue_hours = (now - card.next_review_at).total_seconds() / 3600 if card.next_review_at else 0
            queue.append({
                **self._to_dict(card),
                "priority": round(overdue_hours * (1.0 / max(0.5, card.ease_factor)), 2),
            })
        queue.sort(key=lambda x: x["priority"], reverse=True)
        return queue

    async def batch_create(self, db: AsyncSession, user_id: str, cards: list[dict]) -> list[dict]:
        """批量创建卡片"""
        results = []
        for c in cards:
            try:
                card = await self.create_card(
                    db, user_id,
                    word=c.get("word", ""),
                    lang=c.get("lang", "en"),
                    definition=c.get("definition"),
                    definition_native=c.get("definition_native"),
                    part_of_speech=c.get("part_of_speech"),
                    example_sentence=c.get("example_sentence"),
                    source=c.get("source", "manual"),
                    tags=c.get("tags"),
                    difficulty=c.get("difficulty", 3),
                )
                results.append(card)
            except Exception as e:
                self.logger.warning(f"批量创建卡片失败: {e}")
        return results

    async def get_stats(self, db: AsyncSession, user_id: str, lang: str = "en") -> dict:
        """获取复习统计"""
        now = datetime.now(timezone.utc)

        # 总数
        tr = await db.execute(
            select(func.count(WordCard.id)).where(WordCard.user_id == user_id, WordCard.lang == lang)
        )
        total = tr.scalar() or 0

        # 已掌握
        mr = await db.execute(
            select(func.count(WordCard.id)).where(
                WordCard.user_id == user_id, WordCard.lang == lang,
                WordCard.is_mastered == True,
            )
        )
        mastered = mr.scalar() or 0

        # 待复习
        dr = await db.execute(
            select(func.count(WordCard.id)).where(
                WordCard.user_id == user_id, WordCard.lang == lang,
                WordCard.is_mastered == False,
                WordCard.next_review_at <= now,
            )
        )
        due_today = dr.scalar() or 0

        # 来源分布
        sr = await db.execute(
            select(WordCard.source, func.count(WordCard.id))
            .where(WordCard.user_id == user_id, WordCard.lang == lang)
            .group_by(WordCard.source)
        )
        source_dist = {row[0]: row[1] for row in sr.all()}

        # 总复习次数
        rr = await db.execute(
            select(func.count(WordCardReview.id))
            .join(WordCard, WordCardReview.card_id == WordCard.id)
            .where(WordCard.user_id == user_id, WordCard.lang == lang)
        )
        total_reviews = rr.scalar() or 0

        return {
            "total": total,
            "mastered": mastered,
            "learning": total - mastered,
            "due_today": due_today,
            "mastery_rate": round(mastered / total * 100, 1) if total > 0 else 0,
            "total_reviews": total_reviews,
            "source_distribution": source_dist,
        }

    async def sync_from_companion(self, db: AsyncSession, user_id: str) -> int:
        """从 companion 生词本同步到 word cards"""
        from src.models.companion import CompanionVocabulary

        result = await db.execute(
            select(CompanionVocabulary).where(CompanionVocabulary.user_id == user_id)
        )
        companions = result.scalars().all()

        count = 0
        for cv in companions:
            try:
                await self.create_card(
                    db, user_id,
                    word=cv.word,
                    lang=cv.lang,
                    definition=cv.definition,
                    part_of_speech=cv.part_of_speech,
                    example_sentence=cv.example_sentence,
                    source="companion",
                    source_id=str(cv.id),
                )
                count += 1
            except Exception:
                pass

        self.logger.info(f"从 companion 同步了 {count} 张卡片 (user={user_id})")
        return count

    # ── SM-2 算法 ──

    @staticmethod
    def _schedule_next_review(
        current_interval: float,
        ease_factor: float,
        quality: int,
        review_count: int,
    ) -> tuple[float, float, int, bool]:
        """SM-2 简化版间隔复习调度"""
        if quality < 3:
            # 忘记 → 重置
            next_interval = 4.0
            new_ease = max(1.3, ease_factor - 0.2)
            new_count = 0
            mastered = False
        else:
            if review_count == 0:
                next_interval = 4.0
            elif review_count == 1:
                next_interval = 24.0
            else:
                quality_mult = {0: 0.0, 1: 0.3, 2: 0.6, 3: 1.0, 4: 1.5, 5: 2.0}.get(quality, 1.0)
                next_interval = current_interval * ease_factor * quality_mult

            new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            new_ease = max(1.3, min(2.5, new_ease))
            new_count = review_count + 1

        next_interval = max(1.0, min(8760.0, next_interval))
        mastered = new_count >= 5 and quality >= 4

        return next_interval, new_ease, new_count, mastered

    @staticmethod
    def _to_dict(card: WordCard) -> dict:
        """模型转字典"""
        tags_list = []
        if card.tags:
            try:
                tags_list = json.loads(card.tags)
            except (json.JSONDecodeError, TypeError):
                tags_list = [card.tags] if card.tags else []

        return {
            "id": str(card.id),
            "user_id": card.user_id,
            "word": card.word,
            "lang": card.lang,
            "definition": card.definition,
            "definition_native": card.definition_native,
            "part_of_speech": card.part_of_speech,
            "phonetic": card.phonetic,
            "example_sentence": card.example_sentence,
            "example_translation": card.example_translation,
            "source": card.source,
            "source_id": card.source_id,
            "tags": tags_list,
            "difficulty": card.difficulty,
            "review_count": card.review_count,
            "review_interval_hours": round(card.review_interval_hours, 1),
            "ease_factor": round(card.ease_factor, 2),
            "last_review_at": card.last_review_at.isoformat() if card.last_review_at else None,
            "next_review_at": card.next_review_at.isoformat() if card.next_review_at else None,
            "is_mastered": card.is_mastered,
            "is_favorited": card.is_favorited,
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        }


word_card_service = WordCardService()