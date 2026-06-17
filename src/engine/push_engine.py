"""
LAWA2 — 推送通知引擎
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.push import PushNotification, PushPreference
from src.models.reminder import ReminderEvent as Reminder
from src.models.habit import GrowthMilestone, UserHabitConfig
from src.models.user import User


class PushEngine:
    """推送通知引擎"""

    def __init__(self):
        self._holiday_cache: list[dict] = []

    async def get_or_create_preferences(self, user_id: str) -> PushPreference:
        """获取或创建用户推送偏好"""
        async with AsyncSessionLocal() as session:
            stmt = select(PushPreference).where(PushPreference.user_id == user_id)
            pref = (await session.execute(stmt)).scalar_one_or_none()
            if pref:
                return pref
            pref = PushPreference(user_id=user_id)
            session.add(pref)
            await session.commit()
            return pref

    async def update_preferences(self, user_id: str, **kwargs) -> PushPreference:
        """更新推送偏好"""
        async with AsyncSessionLocal() as session:
            pref = await self.get_or_create_preferences(user_id)
            allowed = {"push_enabled", "reminder_push", "holiday_push", "culture_egg_push",
                       "milestone_push", "daily_feed_push", "morning_time", "noon_time", "evening_time"}
            for key, val in kwargs.items():
                if key in allowed and hasattr(pref, key):
                    setattr(pref, key, val)
            pref.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return pref

    async def get_notifications(self, user_id: str, unread_only: bool = False) -> list[dict]:
        """获取通知列表"""
        async with AsyncSessionLocal() as session:
            stmt = select(PushNotification).where(PushNotification.user_id == user_id)
            if unread_only:
                stmt = stmt.where(PushNotification.is_read == False)
            stmt = stmt.order_by(PushNotification.created_at.desc())
            results = (await session.execute(stmt)).scalars().all()
            return [{
                "id": n.id, "user_id": n.user_id, "title": n.title,
                "title_en": n.title_en, "body": n.body, "body_en": n.body_en,
                "notification_type": n.notification_type,
                "related_event_id": n.related_event_id,
                "is_read": n.is_read, "is_delivered": n.is_delivered,
                "created_at": n.created_at.isoformat(),
                "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
            } for n in results]

    async def mark_read(self, notification_id: str) -> dict:
        """标记通知已读"""
        async with AsyncSessionLocal() as session:
            stmt = select(PushNotification).where(PushNotification.id == notification_id)
            n = (await session.execute(stmt)).scalar_one_or_none()
            if n:
                n.is_read = True
                await session.commit()
                return {"status": "ok"}
            return {"status": "error", "detail": "Not found"}

    async def _generate_daily_challenge(self, user_id: str) -> Optional[dict]:
        """生成每日英文挑战"""
        challenges = [
            {"title": "每日英文挑战 · Daily Challenge", "title_en": "Daily English Challenge",
             "body": "今天用英文说一句：I am making progress every day! 坚持打卡！",
             "body_en": "Say in English today: I am making progress every day! Keep the streak!",
             "type": "daily_feed"},
            {"title": "单词挑战 · Word Challenge", "title_en": "Word Challenge",
             "body": "今天学一个新词：Serendipity (意外发现美好) · 试着用它造个句！",
             "body_en": "Learn a new word: Serendipity (finding something good unexpectedly). Try making a sentence!",
             "type": "daily_feed"},
            {"title": "阅读挑战 · Reading Challenge", "title_en": "Reading Challenge",
             "body": "今天读一篇英文短文（3分钟），记录3个新词！",
             "body_en": "Read a short English article (3 min), record 3 new words!",
             "type": "daily_feed"},
        ]
        challenge = random.choice(challenges)
        return {"title": challenge["title"], "title_en": challenge["title_en"],
                "body": challenge["body"], "body_en": challenge["body_en"], "type": challenge["type"]}

    async def _generate_culture_egg(self) -> Optional[dict]:
        """生成文化彩蛋（节假日背景知识）"""
        eggs = [
            {"title": "文化彩蛋 · Culture Egg", "title_en": "Culture Egg",
             "body": "你知道吗？'Break a leg' 不是真的让你摔断腿，而是祝你好运！源自戏剧界的传统。",
             "body_en": "Did you know? 'Break a leg' doesn't mean actually breaking a leg — it means 'good luck'! Originates from theater traditions.",
             "type": "culture_egg"},
            {"title": "文化彩蛋 · Culture Egg", "title_en": "Culture Egg",
             "body": "美国感恩节（Thanksgiving）起源于1621年，是庆祝丰收和家庭团聚的节日。",
             "body_en": "American Thanksgiving traces back to 1621, celebrating harvest and family reunion.",
             "type": "culture_egg"},
            {"title": "文化彩蛋 · Culture Egg", "title_en": "Culture Egg",
             "body": "在英国，'Queue'（排队）是文化信仰！插队是绝对的禁忌。",
             "body_en": "In the UK, 'queueing' is a cultural belief! Cutting in line is absolutely taboo.",
             "type": "culture_egg"},
        ]
        egg = random.choice(eggs)
        return {"title": egg["title"], "title_en": egg["title_en"],
                "body": egg["body"], "body_en": egg["body_en"], "type": egg["type"]}

    async def _generate_milestone(self, user_id: str) -> Optional[dict]:
        """检查并生成里程碑通知"""
        async with AsyncSessionLocal() as session:
            stmt = select(GrowthMilestone).where(GrowthMilestone.user_id == user_id)
            stmt = stmt.order_by(GrowthMilestone.achieved_at.desc())
            results = (await session.execute(stmt)).scalars().all()
            if results:
                recent = results[0]
                return {
                    "title": f"🎉 成就解锁 · {recent.title}",
                    "title_en": f"🎉 Achievement Unlocked · {recent.title_en}",
                    "body": f"恭喜你完成了「{recent.title}」！XP +{recent.xp_reward}",
                    "body_en": f"Congratulations on completing '{recent.title_en}'! XP +{recent.xp_reward}",
                    "type": "milestone",
                }
            return None

    async def _check_reminders(self, user_id: str) -> list[dict]:
        """检查待办提醒"""
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            stmt = select(Reminder).where(
                and_(Reminder.user_id == user_id,
                     Reminder.remind_time <= now,
                     Reminder.is_completed == False)
            )
            results = (await session.execute(stmt)).scalars().all()
            return [{
                "id": r.id, "title": r.title, "title_en": r.title_en,
                "body": f"提醒你：{r.title} · Reminder: {r.title_en}",
                "body_en": f"Reminder: {r.title_en}",
                "type": "reminder",
                "related_event_id": r.id,
            } for r in results]

    async def check_and_push(self):
        """检查所有用户的推送偏好，生成三段推送"""
        async with AsyncSessionLocal() as session:
            # 获取所有用户
            user_stmt = select(User.id).where(User.is_active == True)
            users = (await session.execute(user_stmt)).scalars().all()

            for user_id in users:
                # 获取用户偏好
                pref_stmt = select(PushPreference).where(PushPreference.user_id == user_id)
                pref = (await session.execute(pref_stmt)).scalar_one_or_none()
                if not pref or not pref.push_enabled:
                    continue

                now = datetime.now(timezone.utc)
                hour = now.hour

                notifications_to_create = []

                # ── 晨间推送 (08:00) ──
                if pref.morning_time == f"{hour:02d}:00":
                    if pref.holiday_push:
                        # 检查今日节假日（使用 reminder_engine 的种子数据）
                        from src.engine.reminder_engine import _get_holidays_for_year
                        now_local = datetime.now()
                        holidays = _get_holidays_for_year(now_local.year)
                        holidays += _get_holidays_for_year(now_local.year + 1)
                        today_holidays = [h for h in holidays if h.get("month") == now_local.month and h.get("day") == now_local.day]
                        for h in today_holidays:
                            notifications_to_create.append({
                                "user_id": user_id,
                                "title": f"🎉 {h.get('name', '节日')} · {h.get('name_en', 'Holiday')}",
                                "title_en": f"🎉 {h.get('name_en', 'Holiday')}",
                                "body": f"今天是{h.get('name', '节日')}！{h.get('culture_background', '')}",
                                "body_en": f"Today is {h.get('name_en', 'Holiday')}! {h.get('culture_background_en', h.get('culture_background', ''))}",
                                "type": "holiday",
                                "related_event_id": h.get("id", ""),
                            })
                    if pref.daily_feed_push:
                        challenge = await self._generate_daily_challenge(user_id)
                        if challenge:
                            notifications_to_create.append({
                                "user_id": user_id,
                                "title": challenge["title"],
                                "title_en": challenge["title_en"],
                                "body": challenge["body"],
                                "body_en": challenge["body_en"],
                                "type": challenge["type"],
                            })

                # ── 午间推送 (12:30) ──
                elif pref.noon_time == f"{hour:02d}:30":
                    if pref.culture_egg_push:
                        egg = await self._generate_culture_egg()
                        if egg:
                            notifications_to_create.append({
                                "user_id": user_id,
                                "title": egg["title"],
                                "title_en": egg["title_en"],
                                "body": egg["body"],
                                "body_en": egg["body_en"],
                                "type": egg["type"],
                            })
                    if pref.reminder_push:
                        reminders = await self._check_reminders(user_id)
                        notifications_to_create.extend(reminders)

                # ── 晚间推送 (20:00) ──
                elif pref.evening_time == f"{hour:02d}:00":
                    if pref.milestone_push:
                        milestone = await self._generate_milestone(user_id)
                        if milestone:
                            notifications_to_create.append({
                                "user_id": user_id,
                                "title": milestone["title"],
                                "title_en": milestone["title_en"],
                                "body": milestone["body"],
                                "body_en": milestone["body_en"],
                                "type": milestone["type"],
                            })

                # 创建通知
                for n_data in notifications_to_create:
                    notification = PushNotification(
                        user_id=n_data["user_id"],
                        title=n_data["title"],
                        title_en=n_data.get("title_en"),
                        body=n_data.get("body"),
                        body_en=n_data.get("body_en"),
                        notification_type=n_data["type"],
                        related_event_id=n_data.get("related_event_id"),
                    )
                    session.add(notification)
                    logger.info(f"推送通知: {n_data['title']} → {user_id}")

                await session.commit()

    async def create_test_notification(self, user_id: str, title: str, body: str, notification_type: str = "reminder") -> dict:
        """创建测试通知"""
        async with AsyncSessionLocal() as session:
            notification = PushNotification(
                user_id=user_id,
                title=title,
                title_en=title,
                body=body,
                body_en=body,
                notification_type=notification_type,
            )
            session.add(notification)
            await session.commit()
            return {"status": "ok", "id": notification.id}


push_engine = PushEngine()