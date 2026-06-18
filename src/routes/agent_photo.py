"""
LAWA2 — 拍照 Agent 入口路由 (/agent/photo)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
from loguru import logger

from src.database.main import get_db
from src.engine.photo_engine import photo_engine, ALLOWED_MIME, MAX_FILE_SIZE
from src.middleware.auth import get_current_user_id

router = APIRouter(prefix="/agent/photo", tags=["photo-agent"])


class ChatRequest(BaseModel):
    message: str


# 认证依赖统一从 src.middleware.auth 导入


@router.get("/health")
async def photo_agent_health():
    """拍照 Agent 健康检查 · Photo Agent Health Check"""
    return {"status": "ok", "agent": "photo", "version": "2.5.0"}


@router.post("/upload")
async def upload_photo(
    file: UploadFile,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """上传图片 + AI 理解 · Upload photo with AI understanding"""
    mime = file.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {mime}")
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大 ({len(file_bytes)} bytes)")
    filename = file.filename or "photo.jpg"
    result = await photo_engine.upload_and_understand(
        user_id=user_id, file_bytes=file_bytes, filename=filename, mime_type=mime, db=db
    )
    return {"status": "ok", "data": result}


@router.get("/history")
async def get_photo_history(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """获取图片历史 · Get photo history"""
    photos = await photo_engine.get_photo_history(user_id=user_id, db=db, limit=limit, offset=offset)
    return {"status": "ok", "data": photos}


@router.get("/{photo_id}")
async def get_photo_detail(
    photo_id: str = Path(..., description="图片ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取图片详情 · Get photo detail"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    return {"status": "ok", "data": result}


@router.get("/{photo_id}/image")
async def get_photo_image(
    photo_id: str = Path(..., description="图片ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取图片文件 · Get photo image"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    image_path = result.get("image_path", "")
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(image_path)


@router.get("/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    photo_id: str = Path(..., description="图片ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取缩略图 · Get photo thumbnail"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    thumb_path = result.get("thumbnail_path", "")
    if not thumb_path or not os.path.exists(thumb_path):
        image_path = result.get("image_path", "")
        if image_path and os.path.exists(image_path):
            return FileResponse(image_path)
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(thumb_path)


@router.post("/{photo_id}/chat")
async def chat_about_photo(
    req: ChatRequest,
    photo_id: str = Path(..., description="图片ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """基于图片对话 · Chat about photo"""
    result = await photo_engine.chat_about_photo(
        photo_id=photo_id, user_id=user_id, message=req.message, db=db
    )
    return {"status": "ok", "data": result}


@router.get("/{photo_id}/chats")
async def get_photo_chats(
    photo_id: str = Path(..., description="图片ID"),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取图片对话历史 · Get photo chat history"""
    chats = await photo_engine.get_photo_chat_history(
        photo_id=photo_id, user_id=user_id, db=db, limit=limit
    )
    return {"status": "ok", "data": chats}


@router.post("/{photo_id}/share")
async def share_photo_to_bridge(
    photo_id: str = Path(..., description="图片ID"),
    target_type: str = Query("greet", description="分享目标类型: greet/teach"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """将图片理解分享到桥梁 · Share photo to bridge"""
    result = await photo_engine.share_to_bridge(
        photo_id=photo_id, user_id=user_id, target_type=target_type
    )
    return {"status": "ok", "data": result}
