"""
LAWA2 — 测试用户管理引擎

自动创建/清理测试用户，用于开发和测试。
测试用户前缀: `test_user_`
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from typing import Optional

# 测试用户前缀
TEST_USER_PREFIX = "test_user_"

# 预设测试用户画像
TEST_USER_PROFILES = [
    {
        "username": "test_user_beginner",
        "display_name": "Beginner Tester",
        "native_lang": "zh",
        "learn_lang": "en",
        "current_level": "beginner",
        "interests": ["daily_conversation", "travel", "food"],
    },
    {
        "username": "test_user_intermediate",
        "display_name": "Intermediate Tester",
        "native_lang": "zh",
        "learn_lang": "en",
        "current_level": "intermediate",
        "interests": ["business", "technology", "culture"],
    },
    {
        "username": "test_user_advanced",
        "display_name": "Advanced Tester",
        "native_lang": "zh",
        "learn_lang": "en",
        "current_level": "advanced",
        "interests": ["academic", "literature", "philosophy"],
    },
]


class TestUserEngine:
    """测试用户管理引擎"""

    @staticmethod
    async def create_test_user(
        db: AsyncSession,
        username: Optional[str] = None,
        profile: Optional[dict] = None,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> User:
        """创建单个测试用户"""
        if username is None:
            username = f"{TEST_USER_PREFIX}{uuid.uuid4().hex[:8]}"
        
        # 检查用户是否已存在
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # 使用提供的 profile 或默认
        if profile is None:
            profile = {
                "display_name": username,
                "native_lang": "zh",
                "learn_lang": "en",
                "current_level": None,
                "interests": [],
            }
        
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            display_name=profile.get("display_name", username),
            native_lang=profile.get("native_lang", "zh"),
            learn_lang=profile.get("learn_lang", "en"),
            current_level=profile.get("current_level"),
            interests=profile.get("interests", []),
            is_admin=is_admin,
            is_active=is_active,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user

    @staticmethod
    async def create_default_test_users(db: AsyncSession) -> list[User]:
        """创建默认测试用户集合"""
        users = []
        for profile in TEST_USER_PROFILES:
            user = await TestUserEngine.create_test_user(db, profile["username"], profile)
            users.append(user)
        return users

    @staticmethod
    async def list_test_users(
        db: AsyncSession,
        prefix: str = TEST_USER_PREFIX,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        """列出所有测试用户"""
        # 获取总数
        total_stmt = select(func.count(User.id)).where(User.username.like(f"{prefix}%"))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()
        
        # 获取用户列表
        stmt = select(User).where(User.username.like(f"{prefix}%")).order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return users, total

    @staticmethod
    async def cleanup_test_users(
        db: AsyncSession,
        prefix: str = TEST_USER_PREFIX,
        older_than_hours: Optional[int] = None,
    ) -> int:
        """清理测试用户"""
        from datetime import timedelta
        
        # 构建删除条件
        conditions = [User.username.like(f"{prefix}%")]
        
        if older_than_hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
            conditions.append(User.created_at <= cutoff)
        
        # 获取要删除的用户
        stmt = select(User).where(*conditions)
        result = await db.execute(stmt)
        users_to_delete = result.scalars().all()
        
        # 删除用户
        for user in users_to_delete:
            await db.delete(user)
        
        await db.commit()
        
        return len(users_to_delete)

    @staticmethod
    async def get_test_user_by_username(
        db: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """根据用户名获取测试用户"""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def delete_test_user(
        db: AsyncSession,
        username: str,
    ) -> bool:
        """删除单个测试用户"""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one()
        
        if not user:
            return False
        
        await db.delete(user)
        await db.commit()
        
        return True

    @staticmethod
    async def reset_test_user(
        db: AsyncSession,
        username: str,
        profile: Optional[dict] = None,
    ) -> Optional[User]:
        """重置测试用户到初始状态"""
        user = await TestUserEngine.get_test_user_by_username(db, username)
        if not user:
            return None
        
        # 重置字段
        user.growth_xp = 0
        user.habit_level = 1
        user.streak_days = 0
        user.bridge_level = 0
        user.last_feed_date = None
        
        # 重置画像
        if profile:
            user.display_name = profile.get("display_name", user.display_name)
            user.native_lang = profile.get("native_lang", user.native_lang)
            user.learn_lang = profile.get("learn_lang", user.learn_lang)
            user.current_level = profile.get("current_level")
            user.interests = profile.get("interests", [])
        
        await db.commit()
        await db.refresh(user)
        
        return user
