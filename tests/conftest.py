"""测试夹具"""
import pytest_asyncio
from src.database.main import init_db, AsyncSessionLocal, Base
from src.models.user import User
from src.models.habit import *


@pytest_asyncio.fixture
async def db_session():
    """测试用数据库会话（每个测试独立）"""
    await init_db()
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
