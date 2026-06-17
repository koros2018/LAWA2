"""
Bridge Engine — 双向桥梁引擎

MVP 策略：用 AI 模拟反向语伴
  - Alice（英→中）看到模拟"Bob"用中文问候，用中文回复
  - Bob（中→英）看到模拟"Alice"用英文问候，用英文回复
  - AI 负责：生成问候语 + 润色回复 + 模拟语伴反馈

参考：docs/LAWA2_ROADMAP.md §4.3（双向桥梁 Lv.1-5）
"""
import random
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import AsyncSessionLocal
from src.models.habit import BridgeInteraction
from src.models.user import User


# ── Lv.1 问候语种子库（中英双向） ──

GREETING_SEEDS = {
    "en": [
        {
            "greeting": "Hey! I heard you're learning English. What's up?",
            "translation": "嘿！听说你在学英文。最近怎么样？",
            "context": "Bob 刚从 Reddit 看到一个有趣帖子，想分享给你",
        },
        {
            "greeting": "Yo! How's your English journey going?",
            "translation": "哟！你的英文之旅怎么样了？",
            "context": "Bob 在刷 Twitter 时想到了你",
        },
        {
            "greeting": "Sup! Just saw a meme and thought of you. Wanna try reading it?",
            "translation": "嘿！刚看到一个 meme 想到了你。想试试能不能读懂？",
            "context": "Bob 在刷 Instagram 时看到一个搞笑 meme",
        },
        {
            "greeting": "Hey there! I've been reading this cool article. Want to check it out together?",
            "translation": "嗨！我在看一篇超酷的文章。要一起看看吗？",
            "context": "Bob 刚读完一篇科技文章，觉得你可能会喜欢",
        },
        {
            "greeting": "What's good? How many new words did you learn today?",
            "translation": "咋样？今天学了多少新词？",
            "context": "Bob 今天也学了 3 个中文词，想比比进度",
        },
    ],
    "zh": [
        {
            "greeting": "嘿，听说你在学中文？要不要一起组个队？",
            "translation": "Hey, heard you're learning Chinese? Want to team up?",
            "context": "Alice 在学中文输入法，想找个语伴",
        },
        {
            "greeting": "你好呀！今天学中文了吗？",
            "translation": "Hi there! Did you study Chinese today?",
            "context": "Alice 刚学会了'加油'，迫不及待想分享",
        },
        {
            "greeting": "嗨！我刚看到一个超好笑的网络用语。你听说过'破防了'吗？",
            "translation": "Hey! I just saw this hilarious internet slang. Heard of 'pò fáng le'?",
            "context": "Alice 在微信群看到了一个搞笑对话",
        },
        {
            "greeting": "你好！我们互相教对方一个词怎么样？我叫 Alice，想学中文。",
            "translation": "Hi! How about we teach each other a word? I'm Alice, learning Chinese.",
            "context": "Alice 觉得交换学习比一个人学有趣",
        },
        {
            "greeting": "晚上好！今天你学了什么有意思的词？",
            "translation": "Good evening! What interesting word did you learn today?",
            "context": "Alice 刚读完一篇文章，想跟你分享她的新词",
        },
    ],
}

# ── Lv.2 点赞桥 — 语伴提问种子 ──

LIKE_PROMPTS = {
    "en": [
        {
            "message": "I just read this: 'AI won't replace you. A person using AI will.' What do you think?",
            "translation": "我刚看到这句话：'AI 不会取代你。会用 AI 的人会。'你觉得呢？",
            "context": "Bob 在 Hacker News 上看到一条热门评论",
        },
        {
            "message": "Check out this meme I found: 'Me trying to learn Chinese vs. me trying to learn math.' 😂",
            "translation": "看我找到的 meme：'学中文的我 vs 学数学的我' 😂",
            "context": "Bob 在刷 Instagram 时收藏了一个 meme",
        },
        {
            "message": "Someone said 'English is just Chinese with different fonts.' What's your take?",
            "translation": "有人说 '英文只是换了字体的中文'。你怎么看？",
            "context": "Bob 在一个论坛上看到这个比喻，觉得很有意思",
        },
    ],
    "zh": [
        {
            "message": "我学会了一句中文：'这个真香'。你觉得我用的对吗？",
            "translation": "I learned a Chinese phrase: 'This is truly fragrant.' Did I use it right?",
            "context": "Alice 昨天在群里看到大家用'真香'，想试试",
        },
        {
            "message": "你看这个：'996是福报'。这句话在中国真的有人这么说吗？",
            "translation": "Look at this: '996 is a blessing.' Do people in China really say that?",
            "context": "Alice 在 Twitter 上看到有人吐槽 996，不太理解",
        },
        {
            "message": "我刚看到中国同事发了一个表情包，一只猫说'我裂开了'。这啥意思？",
            "translation": "I just saw a colleague post a sticker of a cat saying 'I'm cracked.' What does that mean?",
            "context": "Alice 在微信群里看到大家用表情包，想跟你学",
        },
    ],
}

# ── Lv.3 梗桥 — 语伴模仿回复 ──

TEACH_RESPONSES = {
    "en": {
        "curious": [
            "Ohh interesting! Can you use it in a sentence?",
            "Wait, that sounds fun! Give me an example?",
            "I've never heard that one! How do I use it?",
        ],
        "try_use": [
            "Okay I'm gonna try: '{word}' is like... when something is really something? Did I get it?",
            "Let me try: So if I say '{word}', people will know I'm hip? 😎",
            "Testing: '{word}' — did I say it right?",
        ],
        "thanks": [
            "Thanks for teaching me! I'm gonna use this in my next group chat 😄",
            "Nice! I'll add this to my vocab list. My friends will be impressed!",
            "This is gold. I'm gonna impress my Chinese friends with '{word}'!",
        ],
    },
    "zh": {
        "curious": [
            "哇，这个词好有意思！能举个例子吗？",
            "等等，这个听起来好有趣！给我个例句？",
            "我从来没听过这个词！怎么用？",
        ],
        "try_use": [
            "我来试试：'{word}'就是...那个...特别...的那个？我用的对吗？",
            "我试一下：如果我说'{word}'，大家会觉得我懂梗吗？😎",
            "测试：'{word}' — 我没用错吧？",
        ],
        "thanks": [
            "谢谢你教我！我下次在群里就用这个词 😄",
            "太棒了！我要把它加到我的词库里。我朋友一定会被惊到！",
            "绝了！我要用'{word}'去惊艳我的中国朋友们！",
        ],
    },
}


class BridgeEngine:
    """双向桥梁引擎 — 模拟语伴互动"""

    async def get_partner(self, user_id: str) -> dict:
        """获取当前语伴信息"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                return {"partner_id": "bob", "partner_name": "Bob 🇺🇸", "direction": "en"}
            learn_lang = user.learn_lang or "en"
            level = user.bridge_level or 1
            if learn_lang == "zh":
                partner = {
                    "partner_id": "bob",
                    "partner_name": "Bob 🇺🇸",
                    "native_lang": "en",
                    "learn_lang": "zh",
                    "bio": "美国程序员，喜欢科技和 meme，正在学中文想跟中国同事聊天",
                }
            else:
                partner = {
                    "partner_id": "alice",
                    "partner_name": "Alice 🇨🇳",
                    "native_lang": "zh",
                    "learn_lang": "en",
                    "bio": "中国设计师，喜欢美食和旅行，想用英文看懂 Reddit 梗图",
                }
            partner["bridge_level"] = level
            return partner

    async def get_greeting(self, user_id: str) -> dict:
        """Lv.1 获取一条问候语"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            learn_lang = user.learn_lang if user else "en"
            seeds = GREETING_SEEDS.get(learn_lang, GREETING_SEEDS["en"])
            seed = random.choice(seeds)
            if learn_lang == "zh":
                learn_text = seed["greeting"]
                native_text = seed["translation"]
            else:
                learn_text = seed["greeting"]
                native_text = seed["translation"]
            partner = await self.get_partner(user_id)
            interaction = BridgeInteraction(
                user_id=user_id, partner_id=partner["partner_id"],
                level=1, direction="receive",
                native_text=native_text, learn_text=learn_text, partner_reply=native_text,
            )
            session.add(interaction)
            await session.commit()
            return {
                "interaction_id": interaction.id, "partner_name": partner["partner_name"],
                "greeting": learn_text, "translation": native_text,
                "context": seed["context"], "direction": learn_lang,
                "created_at": interaction.created_at.isoformat(),
            }

    async def reply_greeting(self, user_id: str, interaction_id: str, reply_text: str) -> dict:
        """Lv.1 回复问候语 — AI 润色 + 反馈 + 奖励"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.id == interaction_id, BridgeInteraction.user_id == user_id,
            )
            interaction = (await session.execute(stmt)).scalar_one_or_none()
            if not interaction:
                raise ValueError("Interaction not found")
            word_count = len(reply_text.strip())
            if word_count < 2:
                raise ValueError("回复太短了，多说几句吧！")
            polished = reply_text.strip()
            if len(polished) < 10:
                polished = polished + " 😊"
            elif not polished.endswith(("!", "?", "。", "？", "！", ".")):
                polished = polished + "!"
            feedback_pool = [
                "收到啦！你这句话说得真棒 👍", "哈哈 nice！你的表达越来越自然了！",
                "可以的！我完全懂了 👌", "太好了！下次我们试试更难的话题？",
                "说的没错！你进步好快 🎉", "收到！你这句话我要收藏起来学 😄",
            ]
            partner_reply = random.choice(feedback_pool)
            xp_earned = 5
            interaction.polished_text = polished
            interaction.partner_reply = partner_reply
            interaction.xp_earned = xp_earned
            interaction.is_read = True
            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                if not user.bridge_level or user.bridge_level < 1:
                    user.bridge_level = 1
                user.growth_xp = (user.growth_xp or 0) + xp_earned
            await session.commit()
            return {
                "status": "ok", "your_reply": reply_text, "polished": polished,
                "partner_reply": partner_reply, "xp_earned": xp_earned,
            }

    async def get_like_prompt(self, user_id: str) -> dict:
        """Lv.2 点赞桥 — 语伴分享话题让用户评价"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            learn_lang = user.learn_lang if user else "en"
            prompts = LIKE_PROMPTS.get(learn_lang, LIKE_PROMPTS["en"])
            prompt = random.choice(prompts)
            partner = await self.get_partner(user_id)
            interaction = BridgeInteraction(
                user_id=user_id, partner_id=partner["partner_id"],
                level=2, direction="receive",
                native_text=prompt["translation"], learn_text=prompt["message"],
            )
            session.add(interaction)
            await session.commit()
            return {
                "interaction_id": interaction.id, "partner_name": partner["partner_name"],
                "message": prompt["message"], "translation": prompt["translation"],
                "context": prompt["context"], "level": 2, "direction": learn_lang,
                "created_at": interaction.created_at.isoformat(),
            }

    async def like_reply(self, user_id: str, interaction_id: str, reply_text: str) -> dict:
        """Lv.2 用户评价语伴分享的内容"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.id == interaction_id, BridgeInteraction.user_id == user_id,
            )
            interaction = (await session.execute(stmt)).scalar_one_or_none()
            if not interaction:
                raise ValueError("Interaction not found")
            polished = reply_text.strip()
            if len(polished) < 5:
                polished = polished + " 我觉得挺有道理的！"
            feedback_pool = [
                "好观点！你分析得真透彻 👏", "有道理！我之前都没这么想过 🤔",
                "赞！你的想法很有趣，下次我也要试试这么说",
                "厉害了！你这个回复比我的原文还精彩 😄",
                "绝了！你说得太对了，我完全同意 👍",
            ]
            partner_reply = random.choice(feedback_pool)
            xp_earned = 8
            interaction.polished_text = polished
            interaction.partner_reply = partner_reply
            interaction.xp_earned = xp_earned
            interaction.is_read = True
            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                if not user.bridge_level or user.bridge_level < 2:
                    user.bridge_level = 2
                user.growth_xp = (user.growth_xp or 0) + xp_earned
            await session.commit()
            return {
                "status": "ok", "your_reply": reply_text, "polished": polished,
                "partner_reply": partner_reply, "xp_earned": xp_earned,
            }

    async def get_teach_prompt(self, user_id: str) -> dict:
        """Lv.3 梗桥 — 语伴想学一个词"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            learn_lang = user.learn_lang if user else "en"
            partner = await self.get_partner(user_id)
            teach_msgs = {
                "en": {
                    "message": "Hey! I heard there's this cool Chinese internet slang going around. Can you teach me one?",
                    "translation": "嘿！听说有个很酷的中文网络用语。你能教我一个吗？",
                    "context": "Bob 最近在 Reddit 上看到有人讨论中文网络用语，心痒痒",
                },
                "zh": {
                    "message": "Hey! I want to sound more like a native. Can you teach me a cool English slang?",
                    "translation": "嘿！我想说得更地道。你能教我一个酷酷的英文俚语吗？",
                    "context": "Alice 明天要跟外国同事聊天，想学点时髦的说法",
                },
            }
            prompt = teach_msgs.get(learn_lang, teach_msgs["en"])
            interaction = BridgeInteraction(
                user_id=user_id, partner_id=partner["partner_id"],
                level=3, direction="receive",
                native_text=prompt["translation"], learn_text=prompt["message"],
            )
            session.add(interaction)
            await session.commit()
            return {
                "interaction_id": interaction.id, "partner_name": partner["partner_name"],
                "message": prompt["message"], "translation": prompt["translation"],
                "context": prompt["context"], "level": 3, "direction": learn_lang,
                "created_at": interaction.created_at.isoformat(),
            }

    async def teach_word(self, user_id: str, interaction_id: str, word: str, meaning: str, example: str = "") -> dict:
        """Lv.3 用户教语伴一个词，语伴好奇+尝试+感谢"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.id == interaction_id, BridgeInteraction.user_id == user_id,
            )
            interaction = (await session.execute(stmt)).scalar_one_or_none()
            if not interaction:
                raise ValueError("Interaction not found")
            learn_lang = "zh"
            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                learn_lang = user.learn_lang or "en"
            teach = TEACH_RESPONSES.get(learn_lang, TEACH_RESPONSES["en"])
            curious = random.choice(teach["curious"])
            try_use = random.choice(teach["try_use"]).replace("{word}", word)
            thanks = random.choice(teach["thanks"]).replace("{word}", word)
            if example:
                partner_reply = f"{curious}\n\n{try_use}\n\n{thanks}\n\nBTW，你给的例句'{example}'我记下了！"
            else:
                partner_reply = f"{curious}\n\n{try_use}\n\n{thanks}"
            xp_earned = 12
            interaction.polished_text = f"教了语伴一个词「{word}」：{meaning}"
            interaction.partner_reply = partner_reply
            interaction.xp_earned = xp_earned
            interaction.is_read = True
            if user:
                if not user.bridge_level or user.bridge_level < 3:
                    user.bridge_level = 3
                user.growth_xp = (user.growth_xp or 0) + xp_earned
            await session.commit()
            return {
                "status": "ok", "word": word, "meaning": meaning,
                "partner_curious": curious, "partner_try_use": try_use,
                "partner_thanks": thanks, "xp_earned": xp_earned,
            }

    # ── Lv.4 群聊桥 — 模拟多人群聊场景 ──

    GROUP_SCENES = {
        "en": [
            {
                "scene": "📱 WhatsApp 群聊 — 'Weekend Plans'",
                "context": "Bob 把你拉进了一个 WhatsApp 群，里面是他的几个朋友。大家在讨论周末计划。",
                "members": [
                    {"name": "Bob", "role": "你的语伴"},
                    {"name": "Mike", "role": "程序员，爱开玩笑"},
                    {"name": "Sarah", "role": "设计师，喜欢旅行"},
                ],
                "initial_messages": [
                    {"from": "Mike", "text": "Yo! Anyone up for hiking this weekend? The weather's supposed to be sick 🔥"},
                    {"from": "Sarah", "text": "Ooh I'm in! Where are you thinking?"},
                    {"from": "Bob", "text": "Hey you're here! This is my language buddy. Everyone say hi! 👋"},
                ],
            },
            {
                "scene": "💼 Slack 工作群 — 'Project Launch'",
                "context": "你被拉入了一个英文工作群。团队正在讨论产品发布计划。",
                "members": [
                    {"name": "Alex", "role": "项目经理"},
                    {"name": "Jenny", "role": "开发者"},
                    {"name": "Tom", "role": "设计师"},
                ],
                "initial_messages": [
                    {"from": "Alex", "text": "Team, we need to finalize the launch timeline. Any blockers?"},
                    {"from": "Jenny", "text": "Backend is on track. Just waiting for the design assets."},
                    {"from": "Tom", "text": "Designs are 90% done. Should be ready by EOD tomorrow."},
                ],
            },
        ],
        "zh": [
            {
                "scene": "📱 微信群聊 — '周末约饭'",
                "context": "Alice 把你拉进了一个微信群。她的朋友们正在讨论周末聚餐。",
                "members": [
                    {"name": "Alice", "role": "你的语伴"},
                    {"name": "小明", "role": "程序员，吃货"},
                    {"name": "小红", "role": "设计师，喜欢探店"},
                ],
                "initial_messages": [
                    {"from": "小明", "text": "周末了！有人想去吃那家新开的火锅吗？🍲"},
                    {"from": "小红", "text": "我！我！听说他家的毛肚特别好吃"},
                    {"from": "Alice", "text": "嘿，这就是我跟你们说的语伴！大家欢迎一下～ 👋"},
                ],
            },
            {
                "scene": "💼 钉钉工作群 — '项目上线'",
                "context": "你被拉入了一个中文工作群。团队在讨论上线计划。",
                "members": [
                    {"name": "王经理", "role": "项目经理"},
                    {"name": "小李", "role": "后端开发"},
                    {"name": "小张", "role": "前端开发"},
                ],
                "initial_messages": [
                    {"from": "王经理", "text": "大家，上线计划需要确认。有没有什么阻塞？"},
                    {"from": "小李", "text": "后端没问题了，等前端合代码。"},
                    {"from": "小张", "text": "前端快好了，明天中午前能合进去。"},
                ],
            },
        ],
    }

    # ── Lv.5 线下桥 — 模拟真实场景 ──

    OFFLINE_SCENES = {
        "en": [
            {
                "scene": "☕ 咖啡店 — 'Ordering Coffee'",
                "context": "你走进了一家纽约的独立咖啡店。店员正在柜台后等你点单。",
                "npc": {"name": "Barista", "role": "咖啡师"},
                "initial_message": "Hey there! Welcome to Brew Lab. What can I get started for you today?",
            },
            {
                "scene": "🎤 脱口秀 — 'After Show Chat'",
                "context": "你在看一场英文脱口秀。演出结束后，你遇到了其中一位演员。",
                "npc": {"name": "Comedian", "role": "脱口秀演员"},
                "initial_message": "Hey! Thanks for coming tonight. What did you think of the show?",
            },
            {
                "scene": "✈️ 机场 — 'Missed Connection'",
                "context": "你在机场转机，航班延误了。旁边座位的人开始跟你搭话。",
                "npc": {"name": "Fellow Traveler", "role": "同机旅客"},
                "initial_message": "Rough day, huh? Mine's been delayed three hours. You too?",
            },
        ],
        "zh": [
            {
                "scene": "☕ 咖啡馆 — '点单'",
                "context": "你走进了一家上海的小众咖啡馆。店员微笑着等你点单。",
                "npc": {"name": "咖啡师小刘", "role": "咖啡师"},
                "initial_message": "您好！欢迎光临。想喝点什么？",
            },
            {
                "scene": "🏪 便利店 — '结账闲聊'",
                "context": "深夜你在便利店买东西。收银台的大叔看起来很友善。",
                "npc": {"name": "便利店大叔", "role": "收银员"},
                "initial_message": "小伙子/小姑娘，这么晚还买东西啊？加班还是打游戏？😄",
            },
            {
                "scene": "🏥 医院 — '挂号'",
                "context": "你有点不舒服，去社区医院看病。护士在分诊台问你情况。",
                "npc": {"name": "护士姐姐", "role": "分诊护士"},
                "initial_message": "你好，哪里不舒服？来，先量个体温。",
            },
        ],
    }

    async def get_history(self, user_id: str, limit: int = 10) -> list:
        """获取桥梁交互历史"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.user_id == user_id
            ).order_by(BridgeInteraction.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": m.id, "level": m.level, "direction": m.direction,
                    "learn_text": m.learn_text, "native_text": m.native_text,
                    "polished_text": m.polished_text, "partner_reply": m.partner_reply,
                    "xp_earned": m.xp_earned, "created_at": m.created_at.isoformat(),
                }
                for m in result.scalars().all()
            ]

    # ── Lv.4 群聊桥 ──

    async def get_group_prompt(self, user_id: str) -> dict:
        """Lv.4 群聊桥 — 获取一个模拟群聊场景"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            learn_lang = user.learn_lang if user else "en"
            scenes = self.GROUP_SCENES.get(learn_lang, self.GROUP_SCENES["en"])
            scene = random.choice(scenes)
            partner = await self.get_partner(user_id)
            # 生成 scene_text（把消息拼接成一段展示文本）
            messages_text = "\n".join(
                [f"{m['from']}: {m['text']}" for m in scene["initial_messages"]]
            )
            members_text = ", ".join([f"{m['name']}({m['role']})" for m in scene["members"]])
            interaction = BridgeInteraction(
                user_id=user_id, partner_id=partner["partner_id"],
                level=4, direction="receive",
                learn_text=scene["scene"],
                native_text=scene["context"],
            )
            session.add(interaction)
            await session.commit()
            return {
                "interaction_id": interaction.id,
                "partner_name": partner["partner_name"],
                "scene": scene["scene"],
                "context": scene["context"],
                "members": scene["members"],
                "initial_messages": scene["initial_messages"],
                "messages_text": messages_text,
                "members_text": members_text,
                "level": 4,
                "direction": learn_lang,
                "created_at": interaction.created_at.isoformat(),
            }

    async def group_reply(self, user_id: str, interaction_id: str, reply_text: str) -> dict:
        """Lv.4 用户在群里发言，LLM 模拟群友回复"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.id == interaction_id,
                BridgeInteraction.user_id == user_id,
            )
            interaction = (await session.execute(stmt)).scalar_one_or_none()
            if not interaction:
                raise ValueError("Interaction not found")

            from src.services.llm_service import llm_service
            prompt = f"""你是一个AI语伴。以下是一个多人群聊场景：

场景: {interaction.learn_text or '群聊'}

用户刚刚在群里说了一句话："{reply_text}"

请模拟群里的其他成员回复。每个成员回复1-2句话。
回复格式（JSON）：
{{
  "replies": [
    {{"from": "名字", "text": "回复内容"}},
    ...
  ]
}}

让回复自然、有趣，像是真实的群聊互动。如果用户说得不对，可以用友善的方式纠正。"""

            try:
                result = await llm_service.chat_json(
                    messages=[{"role": "user", "content": prompt}],
                    task="bridge",
                    temperature=0.8,
                )
                replies = result.get("replies", [])
            except Exception as e:
                logger.warning(f"LLM群聊回复失败，用种子兜底: {e}")
                replies = [
                    {"from": "Bob", "text": f"Nice! {reply_text[:30]}... I like that! 😄"},
                    {"from": "Sarah", "text": "Totally agree!"},
                ]

            xp_earned = 15
            replies_text = "\n".join([f"{r['from']}: {r['text']}" for r in replies])
            interaction.polished_text = reply_text
            interaction.partner_reply = replies_text
            interaction.xp_earned = xp_earned
            interaction.is_read = True

            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                if not user.bridge_level or user.bridge_level < 4:
                    user.bridge_level = 4
                user.growth_xp = (user.growth_xp or 0) + xp_earned
            await session.commit()

            return {
                "status": "ok",
                "your_reply": reply_text,
                "group_replies": replies,
                "replies_text": replies_text,
                "xp_earned": xp_earned,
            }

    # ── Lv.5 线下桥 ──

    async def get_offline_prompt(self, user_id: str) -> dict:
        """Lv.5 线下桥 — 获取一个模拟现实场景"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            learn_lang = user.learn_lang if user else "en"
            scenes = self.OFFLINE_SCENES.get(learn_lang, self.OFFLINE_SCENES["en"])
            scene = random.choice(scenes)
            partner = await self.get_partner(user_id)
            interaction = BridgeInteraction(
                user_id=user_id, partner_id=partner["partner_id"],
                level=5, direction="receive",
                learn_text=scene["scene"],
                native_text=scene["context"],
            )
            session.add(interaction)
            await session.commit()
            return {
                "interaction_id": interaction.id,
                "partner_name": partner["partner_name"],
                "scene": scene["scene"],
                "context": scene["context"],
                "npc": scene["npc"],
                "initial_message": scene["initial_message"],
                "level": 5,
                "direction": learn_lang,
                "created_at": interaction.created_at.isoformat(),
            }

    async def offline_reply(self, user_id: str, interaction_id: str, reply_text: str) -> dict:
        """Lv.5 用户在场景中回复，LLM 模拟 NPC 回应"""
        async with AsyncSessionLocal() as session:
            stmt = select(BridgeInteraction).where(
                BridgeInteraction.id == interaction_id,
                BridgeInteraction.user_id == user_id,
            )
            interaction = (await session.execute(stmt)).scalar_one_or_none()
            if not interaction:
                raise ValueError("Interaction not found")

            from src.services.llm_service import llm_service
            prompt = f"""你是一个角色扮演助手。以下是一个真实场景：

场景: {interaction.learn_text or '线下互动'}
背景: {interaction.native_text or '一个日常场景'}

NPC 刚才说：需要从上下文中推断。
用户回复："{reply_text}"

请模拟 NPC 继续对话。回复应该自然、符合场景和角色设定。
如果用户表达有误，可以用友善的方式在回复中示范正确说法。

回复格式（JSON）：
{{
  "npc_reply": "NPC的回复内容（1-3句话）",
  "npc_action": "（可选）NPC的小动作，如 '笑了笑' '递过菜单'",
  "culture_tip": "（可选）相关的文化小提示"
}}"""

            try:
                result = await llm_service.chat_json(
                    messages=[{"role": "user", "content": prompt}],
                    task="bridge",
                    temperature=0.8,
                )
                npc_reply = result.get("npc_reply", "")
                npc_action = result.get("npc_action", "")
                culture_tip = result.get("culture_tip", "")
            except Exception as e:
                logger.warning(f"LLM线下回复失败，用种子兜底: {e}")
                npc_reply = f"Got it! {reply_text[:30]}... Cool! Let's continue! 😊"
                npc_action = "微笑着点了点头"
                culture_tip = ""

            xp_earned = 20
            full_reply = npc_reply
            if npc_action:
                full_reply = f"*{npc_action}*\n{npc_reply}"
            if culture_tip:
                full_reply += f"\n\n💡 文化小提示: {culture_tip}"

            interaction.polished_text = reply_text
            interaction.partner_reply = full_reply
            interaction.xp_earned = xp_earned
            interaction.is_read = True

            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                if not user.bridge_level or user.bridge_level < 5:
                    user.bridge_level = 5
                user.growth_xp = (user.growth_xp or 0) + xp_earned
            await session.commit()

            return {
                "status": "ok",
                "your_reply": reply_text,
                "npc_reply": npc_reply,
                "npc_action": npc_action,
                "culture_tip": culture_tip,
                "full_reply": full_reply,
                "xp_earned": xp_earned,
            }

    async def get_progress(self, user_id: str) -> dict:
        """获取桥梁进度"""
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            level = user.bridge_level if user else 0
            cnt_stmt = select(func.count(BridgeInteraction.id)).where(BridgeInteraction.user_id == user_id)
            total_interactions = (await session.execute(cnt_stmt)).scalar() or 0
            xp_stmt = select(func.coalesce(func.sum(BridgeInteraction.xp_earned), 0)).where(BridgeInteraction.user_id == user_id)
            total_xp = (await session.execute(xp_stmt)).scalar() or 0

            lv2_cond = total_interactions >= 3
            lv3_cond = total_interactions >= 6
            lv4_cond = total_interactions >= 10
            lv5_cond = total_interactions >= 15
            return {
                "current_level": level,
                "total_interactions": total_interactions,
                "total_xp": total_xp,
                "next_level_at": f"Lv.2 需要 3 次互动（当前 {total_interactions}/3）" if level < 2
                    else f"Lv.3 需要 6 次互动（当前 {total_interactions}/6）" if level < 3
                    else f"Lv.4 需要 10 次互动（当前 {total_interactions}/10）" if level < 4
                    else f"Lv.5 需要 15 次互动（当前 {total_interactions}/15）" if level < 5
                    else "🎉 已满级！继续互动累积 XP",
                "levels": [
                    {"level": 1, "name": "你好桥 · Greet", "unlocked": level >= 1, "done": total_interactions >= 1},
                    {"level": 2, "name": "点赞桥 · Like", "unlocked": level >= 2 or lv2_cond, "done": total_interactions >= 3},
                    {"level": 3, "name": "梗桥 · Teach", "unlocked": level >= 3 or lv3_cond, "done": total_interactions >= 6},
                    {"level": 4, "name": "群聊桥 · Group", "unlocked": level >= 4 or lv4_cond, "done": total_interactions >= 10},
                    {"level": 5, "name": "线下桥 · Offline", "unlocked": level >= 5 or lv5_cond, "done": total_interactions >= 15},
                ],
            }
