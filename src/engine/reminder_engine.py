"""LAWA2 事项提醒 Agent — 引擎

功能：
1. 提醒事件 CRUD
2. 节假日种子数据（中英双语 + 文化背景）
3. 纪念日自动祝福生成
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from loguru import logger

from src.models.reminder import ReminderEvent
from src.database.main import AsyncSessionLocal


# ── 节假日种子数据（中英双语 + 文化背景） ──

HOLIDAYS: list[dict] = [
    # ── 中国节日 ──
    {
        "title": "元旦",
        "title_en": "New Year's Day",
        "month": 1, "day": 1,
        "culture_background": "公历新年第一天，中国法定节假日，通常放假3天。",
        "culture_background_en": "The first day of the Gregorian calendar year. A public holiday in China, usually a 3-day break.",
    },
    {
        "title": "春节",
        "title_en": "Spring Festival / Chinese New Year",
        "month": 1, "day": 29,
        "culture_background": "中国最重要的传统节日，农历正月初一。家人团聚、吃年夜饭、发红包、放烟花。",
        "culture_background_en": "The most important traditional Chinese festival, on the first day of the lunar calendar. Family reunion, New Year's Eve dinner, red envelopes, fireworks.",
    },
    {
        "title": "元宵节",
        "title_en": "Lantern Festival",
        "month": 2, "day": 12,
        "culture_background": "农历正月十五，春节的最后一天。吃汤圆、赏花灯、猜灯谜。",
        "culture_background_en": "The 15th day of the first lunar month, marking the end of Spring Festival. Eat tangyuan, watch lanterns, solve riddles.",
    },
    {
        "title": "清明节",
        "title_en": "Qingming Festival / Tomb Sweeping Day",
        "month": 4, "day": 4,
        "culture_background": "祭祖扫墓的节日，也是踏青的好时节。",
        "culture_background_en": "A day for ancestor worship and tomb sweeping, also a time for spring outings.",
    },
    {
        "title": "端午节",
        "title_en": "Dragon Boat Festival",
        "month": 5, "day": 31,
        "culture_background": "农历五月初五，纪念屈原。吃粽子、赛龙舟、挂艾草。",
        "culture_background_en": "The 5th day of the 5th lunar month, commemorating Qu Yuan. Eat zongzi, dragon boat races, hang mugwort.",
    },
    {
        "title": "七夕节",
        "title_en": "Qixi Festival / Chinese Valentine's Day",
        "month": 8, "day": 29,
        "culture_background": "农历七月初七，牛郎织女鹊桥相会。中国的「情人节」。",
        "culture_background_en": "The 7th day of the 7th lunar month. The legend of the Cowherd and Weaver Girl crossing the Magpie Bridge. China's 'Valentine's Day'.",
    },
    {
        "title": "中秋节",
        "title_en": "Mid-Autumn Festival",
        "month": 10, "day": 6,
        "culture_background": "农历八月十五，家人团聚赏月。吃月饼、赏桂花、听嫦娥奔月的故事。",
        "culture_background_en": "The 15th day of the 8th lunar month. Family reunion, moon gazing, eat mooncakes, enjoy osmanthus, tell the story of Chang'e.",
    },
    {
        "title": "国庆节",
        "title_en": "National Day",
        "month": 10, "day": 1,
        "culture_background": "中华人民共和国成立纪念日（1949年），黄金周假期。",
        "culture_background_en": "Commemorates the founding of the People's Republic of China (1949). Golden Week holiday.",
    },
    # ── 西方节日 ──
    {
        "title": "情人节",
        "title_en": "Valentine's Day",
        "month": 2, "day": 14,
        "culture_background": "起源于古罗马的圣瓦伦丁节，现在世界各地的情侣互赠礼物表达爱意。",
        "culture_background_en": "Originating from ancient Roman Lupercalia, now a global day for couples to exchange gifts and express love.",
    },
    {
        "title": "愚人节",
        "title_en": "April Fools' Day",
        "month": 4, "day": 1,
        "culture_background": "可以开玩笑和恶作剧的日子，但注意只到中午12点。",
        "culture_background_en": "A day for jokes and pranks — but only until noon!",
    },
    {
        "title": "母亲节",
        "title_en": "Mother's Day",
        "month": 5, "day": 11,
        "culture_background": "五月的第二个星期日，向母亲表达感谢。",
        "culture_background_en": "The second Sunday of May. A day to thank mothers for their love and care.",
    },
    {
        "title": "父亲节",
        "title_en": "Father's Day",
        "month": 6, "day": 15,
        "culture_background": "六月的第三个星期日，向父亲表达敬意。",
        "culture_background_en": "The third Sunday of June. A day to honor fathers and father figures.",
    },
    {
        "title": "万圣节",
        "title_en": "Halloween",
        "month": 10, "day": 31,
        "culture_background": '起源于凯尔特人的萨温节。孩子们装扮成鬼怪挨家要糖——「不给糖就捣蛋」。',
        "culture_background_en": "Originating from the Celtic festival of Samhain. Children dress up as spooky characters and go trick-or-treating.",
    },
    {
        "title": "感恩节",
        "title_en": "Thanksgiving",
        "month": 11, "day": 27,
        "culture_background": "十一月的第四个星期四。家庭聚餐、吃火鸡、表达感恩。",
        "culture_background_en": "The fourth Thursday of November. Family feast, turkey, and expressing gratitude.",
    },
    {
        "title": "圣诞节",
        "title_en": "Christmas",
        "month": 12, "day": 25,
        "culture_background": "纪念耶稣诞生的基督教节日。圣诞树、礼物、圣诞老人、家庭团聚。",
        "culture_background_en": "A Christian holiday commemorating the birth of Jesus. Christmas tree, gifts, Santa Claus, family gatherings.",
    },
    {
        "title": "平安夜",
        "title_en": "Christmas Eve",
        "month": 12, "day": 24,
        "culture_background": "圣诞节前夜，家庭团聚、交换礼物、唱圣诞歌。",
        "culture_background_en": "The evening before Christmas. Family gatherings, gift exchange, caroling.",
    },
    # ── 国际节日 ──
    {
        "title": "世界地球日",
        "title_en": "Earth Day",
        "month": 4, "day": 22,
        "culture_background": "全球性的环保活动日，1970年首次举办。",
        "culture_background_en": "A global environmental movement founded in 1970.",
    },
    {
        "title": "国际劳动节",
        "title_en": "International Workers' Day / Labor Day",
        "month": 5, "day": 1,
        "culture_background": "纪念1886年芝加哥工人运动。中国有3天假期。",
        "culture_background_en": "Commemorates the 1886 Haymarket affair in Chicago. A 3-day holiday in China.",
    },
]


# ── 祝福模板 ──

GREETING_TEMPLATES = {
    "holiday": {
        "zh": "🎉 今天是{title}！{culture}\n你的语伴 Alice 送给你一句：{english_saying}\n\n在中文里我们可以说：「{chinese_wish}」",
        "en": "🎉 Today is {title_en}! {culture_en}\nYour partner Alice has a message for you: {english_saying}\n\nIn English we say: \"{english_wish}\"",
    },
    "birthday": {
        "zh": "🎂 生日快乐！{name}！\n你的语伴 Alice 想对你说：\n「愿你的每一天都像今天一样特别」\n\n英语怎么说？\n\"May your every day be as special as today.\"\n\n试试用英语回复 TA 吧！",
        "en": "🎂 Happy Birthday, {name}! 🎉\nYour partner Alice says:\n\"May your every day be as special as today.\"\n\nTry replying in your target language!",
    },
    "anniversary": {
        "zh": "💝 纪念日快乐！{name}！\n你的语伴 Alice 为你准备了一句话：\n{message}\n\n试试用学到的语言回复吧！",
        "en": "💝 Happy Anniversary, {name}! 🎉\nYour partner Alice has a message for you:\n{message}\n\nTry replying in your target language!",
    },
}


def _get_holidays_for_year(year: int) -> list[dict]:
    """根据月份和日期生成某年的节假日列表"""
    results = []
    for h in HOLIDAYS:
        try:
            d = date(year, h["month"], h["day"])
        except ValueError:
            continue
        results.append({
            "title": h["title"],
            "title_en": h["title_en"],
            "event_date": d,
            "event_type": "holiday",
            "culture_background": h.get("culture_background", ""),
            "culture_background_en": h.get("culture_background_en", ""),
        })
    return results


class ReminderEngine:
    """事项提醒引擎"""

    async def seed_holidays(self, year: int | None = None) -> int:
        """将节假日种子数据写入数据库"""
        if year is None:
            year = date.today().year

        holidays = _get_holidays_for_year(year)
        # 也加明年的
        holidays += _get_holidays_for_year(year + 1)

        async with AsyncSessionLocal() as session:
            count = 0
            for h in holidays:
                # 检查是否已存在
                existing = await session.execute(
                    select(ReminderEvent).where(
                        ReminderEvent.title == h["title"],
                        ReminderEvent.event_date == h["event_date"],
                        ReminderEvent.event_type == "holiday",
                        ReminderEvent.user_id == "__system__",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                event = ReminderEvent(
                    id=str(uuid.uuid4()),
                    user_id="__system__",
                    title=h["title"],
                    title_en=h["title_en"],
                    event_date=h["event_date"],
                    event_type="holiday",
                    culture_background=h.get("culture_background", ""),
                    culture_background_en=h.get("culture_background_en", ""),
                    is_recurring=True,
                    recurring_rule="yearly",
                )
                session.add(event)
                count += 1

            await session.commit()
            logger.info(f"✅ 节假日种子数据已同步：{count} 条")
            return count

    async def list_events(
        self, user_id: str, start_date: date | None = None,
        end_date: date | None = None, event_type: str | None = None,
        include_system: bool = True,
    ) -> list[ReminderEvent]:
        """查询事件列表"""
        async with AsyncSessionLocal() as session:
            query = select(ReminderEvent)

            # 用户自己的 + 系统节假日
            if include_system:
                query = query.where(
                    ReminderEvent.user_id.in_([user_id, "__system__"])
                )
            else:
                query = query.where(ReminderEvent.user_id == user_id)

            if start_date:
                query = query.where(ReminderEvent.event_date >= start_date)
            if end_date:
                query = query.where(ReminderEvent.event_date <= end_date)
            if event_type:
                query = query.where(ReminderEvent.event_type == event_type)

            query = query.order_by(ReminderEvent.event_date)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_event(self, event_id: str) -> ReminderEvent | None:
        """获取单个事件"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ReminderEvent).where(ReminderEvent.id == event_id)
            )
            return result.scalar_one_or_none()

    async def create_event(
        self, user_id: str, title: str, event_date: date,
        title_en: str | None = None, event_type: str = "personal",
        note: str | None = None, note_en: str | None = None,
        is_recurring: bool = False, recurring_rule: str | None = None,
    ) -> ReminderEvent:
        """创建事件"""
        async with AsyncSessionLocal() as session:
            event = ReminderEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                title_en=title_en or title,
                event_date=event_date,
                event_type=event_type,
                note=note,
                note_en=note_en or note,
                is_recurring=is_recurring,
                recurring_rule=recurring_rule,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    async def update_event(
        self, event_id: str, **kwargs,
    ) -> ReminderEvent | None:
        """更新事件"""
        async with AsyncSessionLocal() as session:
            event = await session.get(ReminderEvent, event_id)
            if not event:
                return None
            for key, value in kwargs.items():
                if hasattr(event, key) and value is not None:
                    setattr(event, key, value)
            await session.commit()
            await session.refresh(event)
            return event

    async def delete_event(self, event_id: str) -> bool:
        """删除事件"""
        async with AsyncSessionLocal() as session:
            event = await session.get(ReminderEvent, event_id)
            if not event:
                return False
            await session.delete(event)
            await session.commit()
            return True

    async def get_upcoming(self, user_id: str, days: int = 7) -> list[ReminderEvent]:
        """获取即将到来的事件"""
        today = date.today()
        end = today + timedelta(days=days)
        return await self.list_events(
            user_id, start_date=today, end_date=end,
        )

    async def get_today(self, user_id: str) -> list[ReminderEvent]:
        """获取今日事件"""
        today = date.today()
        return await self.list_events(
            user_id, start_date=today, end_date=today,
        )

    async def generate_greeting(
        self, event_id: str, user_name: str = "你",
    ) -> dict | None:
        """为纪念日生成祝福语"""
        event = await self.get_event(event_id)
        if not event:
            return None

        if event.event_type == "holiday":
            # 找对应的节假日模板
            h = next(
                (h for h in HOLIDAYS if h["title"] == event.title),
                None,
            )
            if h:
                return {
                    "zh": GREETING_TEMPLATES["holiday"]["zh"].format(
                        title=event.title,
                        culture=event.culture_background or "",
                        english_saying="Happy holidays! 🎉",
                        chinese_wish=f"节日快乐！",
                    ),
                    "en": GREETING_TEMPLATES["holiday"]["en"].format(
                        title_en=event.title_en or event.title,
                        culture_en=event.culture_background_en or "",
                        english_saying="Happy holidays! 🎉",
                        english_wish="Happy holidays!",
                    ),
                }
        elif event.event_type == "anniversary":
            return {
                "zh": GREETING_TEMPLATES["anniversary"]["zh"].format(
                    name=user_name,
                    message="每一个和你在一起的日子都值得庆祝",
                ),
                "en": GREETING_TEMPLATES["anniversary"]["en"].format(
                    name=user_name,
                    message="Every day with you is worth celebrating",
                ),
            }

        # 默认祝福
        return {
            "zh": f"🎉 今天是{event.title}！祝{user_name}一切顺利！",
            "en": f"🎉 Today is {event.title_en or event.title}! Wishing {user_name} all the best!",
        }


# 单例
reminder_engine = ReminderEngine()
