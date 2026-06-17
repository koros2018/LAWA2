"""
LAWA2 — 种子语料管理路由

管理用户自定义的社交场景、推送文案、文化背景等内容。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.engine.seed_content_engine import SeedContentEngine
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api/v2/seed", tags=["seed-content"])


from src.middleware.auth_middleware import get_current_user


# ── Request/Response Models ──

class SeedContentCreate(BaseModel):
    content_type: str = Field(..., description="内容类型: social_scene | push_message | culture_tip | holiday_info | vocabulary_card")
    title: str = Field(..., description="中文标题")
    title_en: str = Field(..., description="英文标题")
    content: Optional[str] = Field(None, description="中文内容")
    content_en: Optional[str] = Field(None, description="英文内容")
    tags: Optional[list[str]] = Field(None, description="标签列表")
    difficulty: Optional[str] = Field(None, description="难度: beginner | intermediate | advanced")


class SeedContentUpdate(BaseModel):
    title: Optional[str] = Field(None, description="中文标题")
    title_en: Optional[str] = Field(None, description="英文标题")
    content: Optional[str] = Field(None, description="中文内容")
    content_en: Optional[str] = Field(None, description="英文内容")
    tags: Optional[list[str]] = Field(None, description="标签列表")
    difficulty: Optional[str] = Field(None, description="难度")
    is_active: Optional[bool] = Field(None, description="是否启用")


class SeedContentListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


# ── Routes ──

@router.get("/contents", response_model=SeedContentListResponse)
def list_seed_contents(
    current_user: User = Depends(get_current_user),
    content_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """列出种子语料"""
    contents, total = SeedContentEngine.list_contents(
        db=db,
        user_id=current_user.id,
        content_type=content_type,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return SeedContentListResponse(
        items=[c.to_dict() for c in contents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/contents/{content_id}")
def get_seed_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个种子语料"""
    content = SeedContentEngine.get_content(db=db, user_id=current_user.id, content_id=content_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content.to_dict()


@router.post("/contents")
def create_seed_content(
    data: SeedContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建种子语料"""
    content = SeedContentEngine.create_content(
        db=db,
        user_id=current_user.id,
        content_type=data.content_type,
        title=data.title,
        title_en=data.title_en,
        content=data.content,
        content_en=data.content_en,
        tags=data.tags,
        difficulty=data.difficulty,
    )
    return content.to_dict()


@router.put("/contents/{content_id}")
def update_seed_content(
    content_id: int,
    data: SeedContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新种子语料"""
    content = SeedContentEngine.update_content(
        db=db,
        user_id=current_user.id,
        content_id=content_id,
        title=data.title,
        title_en=data.title_en,
        content=data.content,
        content_en=data.content_en,
        tags=data.tags,
        difficulty=data.difficulty,
        is_active=data.is_active,
    )
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在或为系统内置")
    return content.to_dict()


@router.delete("/contents/{content_id}")
def delete_seed_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除种子语料"""
    success = SeedContentEngine.delete_content(db=db, user_id=current_user.id, content_id=content_id)
    if not success:
        raise HTTPException(status_code=404, detail="内容不存在或为系统内置")
    return {"message": "已删除 · Deleted ✓", "content_id": content_id}


@router.get("/contents/system/{content_type}")
def get_system_contents(
    content_type: str,
    db: Session = Depends(get_db),
):
    """获取系统内置种子语料（无需认证）"""
    contents = SeedContentEngine.get_system_contents(db=db, content_type=content_type)
    return {"items": [c.to_dict() for c in contents], "total": len(contents)}
