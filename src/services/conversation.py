"""
LAWA2 对话服务 v5.0.0
提供智能纠错、语境扩展、多轮记忆功能

依赖 src.models.conversation 中的 ORM 模型。
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation, ConversationMessage, Correction
from src.services.llm_service import LLMService


# ── Pydantic 模型 ──

class ConversationCreateBody:
    """创建对话参数"""
    def __init__(self, user_id: str, topic: str = None, partner_id: int = None):
        self.user_id = user_id
        self.topic = topic
        self.partner_id = partner_id


class MessageBody:
    """消息参数"""
    def __init__(self, role: str, content: str, content_en: str = None):
        self.role = role
        self.content = content
        self.content_en = content_en


# ── 对话服务 ──

class ConversationService:
    """对话服务：CRUD + 多轮记忆"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, user_id: str, topic: str = None, partner_id: int = None) -> Conversation:
        """创建新对话"""
        conversation = Conversation(
            user_id=user_id,
            topic=topic,
            partner_id=partner_id,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """获取单个对话（含消息）"""
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages_list))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_user_conversations(self, user_id: str, limit: int = 20) -> list[Conversation]:
        """获取用户对话列表（不含消息体）"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        content_en: str = None,
    ) -> ConversationMessage:
        """添加消息到对话"""
        # 获取当前最大 order
        result = await self.db.execute(
            select(func.max(ConversationMessage.order))
            .where(ConversationMessage.conversation_id == conversation_id)
        )
        max_order = result.scalar() or 0

        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            content_en=content_en,
            order=max_order + 1,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)

        # 更新对话的 word_count 和 updated_at
        word_count = count_words(content) + (count_words(content_en or "") if content_en else 0)
        conv = await self.db.get(Conversation, conversation_id)
        if conv:
            conv.word_count = (conv.word_count or 0) + word_count
            conv.updated_at = datetime.now(timezone.utc)

        return msg

    async def get_messages(self, conversation_id: int, limit: int = 50) -> list[ConversationMessage]:
        """获取对话消息列表"""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.order.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话（级联删除消息和纠错记录）"""
        # 删除纠错记录
        await self.db.execute(
            delete(Correction).where(Correction.conversation_id == conversation_id)
        )
        # 删除消息
        await self.db.execute(
            delete(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)
        )
        # 删除对话
        result = await self.db.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        return result.rowcount > 0


# ── 纠错服务 ──

class CorrectionService:
    """纠错记录服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_correction(
        self,
        conversation_id: int,
        original: str,
        corrected: str,
        explanation: str = None,
        word_diff: dict = None,
    ) -> Correction:
        """创建纠错记录"""
        corr = Correction(
            conversation_id=conversation_id,
            original=original,
            corrected=corrected,
            explanation=explanation,
            word_diff=word_diff or {},
        )
        self.db.add(corr)
        await self.db.flush()
        await self.db.refresh(corr)
        return corr

    async def get_corrections(self, conversation_id: int, limit: int = 50) -> list[Correction]:
        """获取对话的纠错记录"""
        result = await self.db.execute(
            select(Correction)
            .where(Correction.conversation_id == conversation_id)
            .order_by(Correction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# ── AI 对话生成器 ──

class AIDialogueGenerator:
    """AI 对话生成器（基于 DeepSeek API / LLMService）

    提供：
    - 智能纠错（纠正语法/用词错误）
    - 语境扩展（主动拓展话题）
    - 多轮记忆（记住对话上下文）
    """

    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.llm = LLMService()

    async def generate_response(
        self,
        messages: list[dict],
        user_level: int = 1,
        enable_correction: bool = True,
        topic: str = None,
    ) -> dict:
        """
        生成 AI 回复

        Args:
            messages: 对话历史 [{role, content, content_en}]
            user_level: 用户语言水平 1-5
            enable_correction: 是否启用纠错
            topic: 对话主题

        Returns:
            {
                "content": "中文回复",
                "content_en": "英文回复",
                "correction": { original, corrected, explanation } | None
            }
        """
        system_prompt = self._build_system_prompt(user_level, enable_correction, topic)
        formatted = self._format_messages(messages, system_prompt)

        # 调用 LLM 服务
        try:
            response = await self.llm.chat(
                messages=formatted,
                model=self.model,
                temperature=0.7,
            )
        except Exception as e:
            # 降级：返回模拟响应
            last = messages[-1]["content"] if messages else ""
            response = self._fallback_response(last, user_level, enable_correction)

        # 解析响应
        return self._parse_response(response, messages, enable_correction)

    def _build_system_prompt(self, level: int, enable_correction: bool, topic: str = None) -> str:
        """构建系统提示词"""
        level_descriptions = {
            1: "Beginner — simple sentences, basic vocabulary",
            2: "Elementary — simple conversations, common phrases",
            3: "Intermediate — more complex sentences, varied vocabulary",
            4: "Advanced — complex expressions, idioms, nuanced grammar",
            5: "Proficient — native-like fluency, cultural references, humor",
        }

        prompt_parts = [
            "You are a bilingual language learning assistant for LAWA2.",
            f"User language level: {level} — {level_descriptions.get(level, 'Unknown')}",
            "",
            "Rules:",
            "1. Always respond in BOTH Chinese and English.",
            "2. Match the user's language level — don't overcomplicate.",
            "3. Be friendly, encouraging, and conversational.",
            "4. If the user writes in mixed language, match their mix.",
            "5. Keep responses concise (2-4 sentences per language).",
        ]

        if enable_correction:
            prompt_parts.append("")
            prompt_parts.append("Correction mode is ON:")
            prompt_parts.append("- If the user makes grammar/spelling errors, gently correct them.")
            prompt_parts.append("- Provide a brief explanation for each correction.")
            prompt_parts.append("- Format corrections as: [original → corrected] with reason.")
            prompt_parts.append("- Don't over-correct — only fix real errors.")

        if topic:
            prompt_parts.append("")
            prompt_parts.append(f"Conversation topic: {topic}")
            prompt_parts.append("Stay on topic but feel free to expand naturally.")

        prompt_parts.append("")
        prompt_parts.append("Respond in JSON format:")
        prompt_parts.append('{"content": "Chinese reply", "content_en": "English reply"')
        if enable_correction:
            prompt_parts.append(', "correction": {"original": "wrong text", "corrected": "fixed text", "explanation": "why it was wrong"}')
        prompt_parts.append("}")

        return "\n".join(prompt_parts)

    def _format_messages(self, messages: list[dict], system_prompt: str) -> list[dict]:
        """格式化消息为 LLM 输入"""
        formatted = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            content = msg.get("content", "")
            content_en = msg.get("content_en", "")
            if content_en:
                content = f"{content}\n\n(English: {content_en})"
            formatted.append({"role": msg.get("role", "user"), "content": content})
        return formatted

    def _parse_response(self, response: str, messages: list, enable_correction: bool) -> dict:
        """解析 LLM 响应"""
        result = {
            "content": "",
            "content_en": "",
            "correction": None,
        }

        # 尝试解析 JSON
        try:
            parsed = json.loads(response)
            result["content"] = parsed.get("content", "")
            result["content_en"] = parsed.get("content_en", "")
            if enable_correction:
                result["correction"] = parsed.get("correction")
        except (json.JSONDecodeError, TypeError):
            # 非 JSON 格式，提取中英文
            lines = response.strip().split("\n")
            chinese = []
            english = []
            current = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re.search(r'[\u4e00-\u9fff]', line) and not current:
                    chinese.append(line)
                elif re.search(r'[a-zA-Z]{3,}', line):
                    english.append(line)
                elif current == "en":
                    english.append(line)
                else:
                    chinese.append(line)

            result["content"] = "\n".join(chinese) or response
            result["content_en"] = "\n".join(english) or response

        return result

    def _fallback_response(self, last_message: str, level: int, enable_correction: bool) -> str:
        """降级响应（LLM 不可用时）"""
        responses = [
            "That's interesting! Tell me more about it. / 真有意思！能再多说说吗？",
            "I see what you mean. Let's explore this topic further. / 我明白你的意思了。我们继续聊聊这个话题吧。",
            "Great point! Here's something to think about... / 说得好！这里有个值得思考的角度...",
            "I appreciate your thoughts on this. Let me share my perspective. / 感谢你的分享。让我也说说我的看法。",
        ]
        import random
        text = random.choice(responses)
        return json.dumps({
            "content": text.split("/")[-1].strip(),
            "content_en": text.split("/")[0].strip(),
            "correction": None,
        })


# ── 工具函数 ──

def count_words(text: str) -> int:
    """统计词汇量（中文按字符，英文按单词）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    return chinese_chars + english_words


def extract_keywords(text: str, max_words: int = 20) -> list[str]:
    """提取关键词"""
    # 中文词
    chinese = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    # 英文词
    english = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    # 去重并限制数量
    seen = set()
    words = []
    for w in chinese + english:
        w_lower = w.lower()
        if w_lower not in seen:
            seen.add(w_lower)
            words.append(w)
            if len(words) >= max_words:
                break
    return words
