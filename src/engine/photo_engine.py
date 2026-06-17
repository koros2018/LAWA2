"""
LAWA2 — 拍照理解引擎

核心逻辑：
1. 图片上传 → 存储 + 缩略图
2. AI 理解 → 中英双语描述 + 关键词提取 + 场景标签
3. 基于图片的中英对话

图片存储在：./uploads/photos/
"""
import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.models.photo import PhotoUnderstanding, PhotoChat
from src.models.habit import BridgeInteraction
from src.models.user import User
from src.database.main import AsyncSessionLocal
from src.services.llm_service import llm_service
from fastapi import HTTPException


# ── 存储路径 ──
UPLOAD_DIR = Path("./uploads/photos")
THUMBNAIL_DIR = Path("./uploads/photos/thumbnails")

# 允许的图片类型
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "image/bmp", "image/tiff",
}

# 图片大小限制 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def _utcnow():
    return datetime.now(timezone.utc)


def _ensure_dirs():
    """确保上传目录存在"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


# ── 场景分类提示词 ──
SCENE_SYSTEM_PROMPT = """你是一个图片场景分类助手。根据用户对图片的描述，判断图片所属的场景类型。

从以下标签中选择最匹配的1-3个（用英文标签）：
food, landscape, architecture, portrait, pet, nature, technology,
urban, art, transportation, daily_life, document, screenshot, other

返回JSON格式：{"tags": ["tag1", "tag2"], "zh": "中文场景名", "en": "English scene name"}"""


class PhotoEngine:
    """拍照理解引擎"""

    async def upload_and_understand(
        self,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        db: AsyncSession,
    ) -> dict:
        """上传图片 + AI 理解（完整流程）"""
        # 1. 验证
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"文件过大: {len(file_bytes)} bytes (上限 {MAX_FILE_SIZE})")
        if mime_type not in ALLOWED_MIME:
            raise ValueError(f"不支持的文件类型: {mime_type}")

        # 2. 保存文件
        _ensure_dirs()
        ext = Path(filename).suffix or ".jpg"
        file_id = str(uuid.uuid4())
        save_name = f"{file_id}{ext}"
        save_path = UPLOAD_DIR / save_name

        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # 生成缩略图
        thumbnail_path = self._generate_thumbnail(save_path, file_id, ext)

        logger.info(f"📸 图片已保存: {save_path} ({len(file_bytes)} bytes) 缩略图: {thumbnail_path}")

        # 3. AI 理解（中英双语描述 + 关键词 + 场景）
        description_zh, description_en, keywords, scene_tags = await self._ai_understand(file_bytes, filename)

        # 4. 存入数据库
        photo = PhotoUnderstanding(
            user_id=user_id,
            image_path=str(save_path),
            thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
            original_filename=filename,
            file_size=len(file_bytes),
            mime_type=mime_type,
            ai_description=description_zh,
            ai_description_en=description_en,
            extracted_words=keywords,
            scene_tags=scene_tags,
        )
        db.add(photo)
        await db.commit()
        await db.refresh(photo)

        logger.info(f"📸 AI理解完成: {description_zh[:60]}... (场景: {scene_tags})")

        return self._photo_to_dict(photo)

    def _generate_thumbnail(self, source_path: Path, file_id: str, ext: str) -> Optional[Path]:
        """生成缩略图 (200px宽, 保持比例)"""
        try:
            from PIL import Image
            thumb_dir = THUMBNAIL_DIR
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb_path = thumb_dir / f"{file_id}{ext}"
            if not source_path.exists():
                return None
            img = Image.open(source_path)
            w, h = img.size
            if w > 200:
                new_h = int(h * 200 / w)
                img = img.resize((200, new_h), Image.LANCZOS)
            img.save(thumb_path, quality=75)
            logger.info(f"🖼️ 缩略图已生成: {thumb_path}")
            return thumb_path
        except ImportError:
            logger.warning("Pillow 未安装，跳过缩略图生成")
            return None
        except Exception as e:
            logger.warning(f"缩略图生成失败: {e}")
            return None

    async def _ai_understand(
        self,
        image_bytes: bytes,
        filename: str,
    ) -> tuple[str, str, list[dict], list[str]]:
        """AI 理解图片内容

        由于当前 LLM 不支持直接图片输入，改为让用户提供简短描述
        AI 基于用户描述生成中英双语内容。

        返回: (description_zh, description_en, keywords, scene_tags)
        """
        # 暂不支持直接图片识别（需要多模态模型）
        # 返回基础占位信息，后续由 chat 流程补充
        placeholder_zh = f"你上传了一张图片: {filename}。让我看看……"
        placeholder_en = f"You uploaded an image: {filename}. Let me take a look..."

        # 尝试用 LLM 识别场景（基于文件名推测）
        try:
            scene_result = await llm_service.chat_json(
                messages=[
                    {"role": "system", "content": SCENE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"用户上传了一张图片，文件名是: {filename}"},
                ],
                task="simple",
                temperature=0.3,
            )
            tags = scene_result.get("tags", ["other"])
            scene_zh = scene_result.get("zh", "其他")
            scene_en = scene_result.get("en", "Other")
            scene_tags = tags
            description_zh = f"这是一张{scene_zh}类图片。{placeholder_zh}"
            description_en = f"This is a {scene_en} image. {placeholder_en}"
        except Exception as e:
            logger.warning(f"场景识别失败: {e}")
            scene_tags = ["other"]
            description_zh = placeholder_zh
            description_en = placeholder_en

        # 提取关键词
        try:
            kw_result = await llm_service.chat_json(
                messages=[
                    {"role": "system", "content": """从图片描述中提取3-5个关键词。
返回JSON格式: {"words": [{"word": "单词", "zh": "中文释义", "en": "English meaning", "example": "例句"}]}"""},
                    {"role": "user", "content": f"图片描述(中文): {description_zh}\n图片描述(英文): {description_en}"},
                ],
                task="simple",
                temperature=0.3,
            )
            keywords = kw_result.get("words", [])
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            keywords = []

        return description_zh, description_en, keywords, scene_tags

    async def chat_about_photo(
        self,
        photo_id: str,
        user_id: str,
        message: str,
        db: AsyncSession,
    ) -> dict:
        """基于图片的对话"""
        # 1. 查找图片记录
        result = await db.execute(
            select(PhotoUnderstanding).where(
                PhotoUnderstanding.id == photo_id,
                PhotoUnderstanding.user_id == user_id,
            )
        )
        photo = result.scalar_one_or_none()
        if not photo:
            raise ValueError(f"图片不存在: {photo_id}")

        # 2. 获取最近对话历史
        chat_result = await db.execute(
            select(PhotoChat)
            .where(PhotoChat.photo_id == photo_id)
            .order_by(desc(PhotoChat.created_at))
            .limit(10)
        )
        history = chat_result.scalars().all()[::-1]  # 正序

        # 3. 构建对话上下文
        system_prompt = f"""你是LAWA2的拍照理解Agent。用户上传了一张图片。

图片描述（中文）: {photo.ai_description}
图片描述（英文）: {photo.ai_description_en}
场景标签: {', '.join(photo.scene_tags)}
关键词: {json.dumps(photo.extracted_words, ensure_ascii=False)}

你的任务是：
1. 始终用中英双语回复用户（中文 + English）
2. 基于图片内容展开自然对话
3. 可以在回复中自然融入关键词的双语释义
4. 保持对话轻松有趣，像朋友聊天

回复格式：先说中文，换行后说英文。"""

        messages = [{"role": "system", "content": system_prompt}]

        # 加入历史对话
        for msg in history:
            role = "assistant" if msg.role == "assistant" else "user"
            content = msg.content
            if msg.content_en:
                content += f"\n{msg.content_en}"
            messages.append({"role": role, "content": content})

        # 加入用户最新消息
        messages.append({"role": "user", "content": message})

        # 4. AI 回复
        try:
            reply = await llm_service.chat(
                messages=messages,
                task="companion",
                temperature=0.7,
                max_tokens=512,
            )
        except Exception as e:
            logger.error(f"图片对话失败: {e}")
            reply = "抱歉，我暂时无法回复。请稍后再试。\nSorry, I can't reply right now. Please try again later."

        # 5. 解析中英双语（简单分割）
        parts = reply.split("\n", 1)
        content_zh = parts[0] if parts else reply
        content_en = parts[1] if len(parts) > 1 else ""

        # 6. 保存对话
        # 用户消息
        user_chat = PhotoChat(
            photo_id=photo_id,
            role="user",
            content=message,
        )
        db.add(user_chat)

        # AI 回复
        assistant_chat = PhotoChat(
            photo_id=photo_id,
            role="assistant",
            content=content_zh,
            content_en=content_en,
        )
        db.add(assistant_chat)

        # 更新对话计数
        photo.chat_count = (photo.chat_count or 0) + 2

        await db.commit()
        await db.refresh(assistant_chat)

        return {
            "id": assistant_chat.id,
            "role": "assistant",
            "content": content_zh,
            "content_en": content_en,
            "created_at": assistant_chat.created_at.isoformat(),
        }

    async def get_photo_detail(
        self,
        photo_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> Optional[dict]:
        """获取图片详情"""
        result = await db.execute(
            select(PhotoUnderstanding).where(
                PhotoUnderstanding.id == photo_id,
                PhotoUnderstanding.user_id == user_id,
            )
        )
        photo = result.scalar_one_or_none()
        if not photo:
            return None
        return self._photo_to_dict(photo)

    async def get_photo_chat_history(
        self,
        photo_id: str,
        user_id: str,
        db: AsyncSession,
        limit: int = 20,
    ) -> list[dict]:
        """获取图片对话历史"""
        # 验证图片归属
        result = await db.execute(
            select(PhotoUnderstanding).where(
                PhotoUnderstanding.id == photo_id,
                PhotoUnderstanding.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError(f"图片不存在: {photo_id}")

        chat_result = await db.execute(
            select(PhotoChat)
            .where(PhotoChat.photo_id == photo_id)
            .order_by(desc(PhotoChat.created_at))
            .limit(limit)
        )
        chats = chat_result.scalars().all()[::-1]

        return [
            {
                "id": c.id,
                "role": c.role,
                "content": c.content,
                "content_en": c.content_en,
                "created_at": c.created_at.isoformat(),
            }
            for c in chats
        ]

    async def get_photo_history(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """获取用户的历史图片列表"""
        result = await db.execute(
            select(PhotoUnderstanding)
            .where(PhotoUnderstanding.user_id == user_id)
            .order_by(desc(PhotoUnderstanding.created_at))
            .offset(offset)
            .limit(limit)
        )
        photos = result.scalars().all()
        return [self._photo_to_dict(p) for p in photos]

    def _photo_to_dict(self, photo: PhotoUnderstanding) -> dict:
        return {
            "id": photo.id,
            "user_id": photo.user_id,
            "image_path": photo.image_path,
            "original_filename": photo.original_filename,
            "file_size": photo.file_size,
            "mime_type": photo.mime_type,
            "ai_description": photo.ai_description,
            "ai_description_en": photo.ai_description_en,
            "extracted_words": photo.extracted_words or [],
            "scene_tags": photo.scene_tags or [],
            "thumbnail_path": photo.thumbnail_path,
            "chat_count": photo.chat_count or 0,
            "created_at": photo.created_at.isoformat(),
        }

    async def share_to_bridge(self, photo_id: str, user_id: str, target_type: str = "greet") -> dict:
        """将图片理解分享到桥梁对话
        target_type: greet/like/teach/group/offline
        """
        async with AsyncSessionLocal() as session:
            # 1. 获取图片理解
            stmt = select(PhotoUnderstanding).where(PhotoUnderstanding.id == photo_id)
            understanding = (await session.execute(stmt)).scalar_one_or_none()
            if not understanding:
                raise HTTPException(status_code=404, detail="图片理解不存在")

            # 2. 获取图片
            img_stmt = select(Photo).where(Photo.id == understanding.photo_id)
            photo = (await session.execute(img_stmt)).scalar_one_or_none()

            # 3. 创建桥梁交互记录
            interaction = BridgeInteraction(
                user_id=user_id,
                partner_name="AI 语伴",
                message=understanding.description,
                translation=understanding.description_en,
                context=f"来自照片理解: {photo.description if photo else ''}",
                direction="out",
                level=target_type,
            )
            session.add(interaction)

            # 4. 更新用户 XP
            user_stmt = select(User).where(User.id == user_id)
            user = (await session.execute(user_stmt)).scalar_one_or_none()
            if user:
                user.growth_xp = (user.growth_xp or 0) + 10

            await session.commit()

            return {
                "status": "ok",
                "interaction_id": interaction.id,
                "xp_earned": 10,
                "message": f"已将「{understanding.description[:20]}...」分享到桥梁 {target_type}",
            }


# 全局单例
photo_engine = PhotoEngine()
