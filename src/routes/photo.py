"""
LAWA2 — 拍照理解 Agent API

端点:
  POST   /api/v2/photo/upload     — 上传图片 + AI 理解
  POST   /api/v2/photo/:id/chat   — 基于图片对话
  GET    /api/v2/photo/:id        — 图片详情
  GET    /api/v2/photo/:id/chats  — 对话历史
  GET    /api/v2/photo/history    — 历史图片列表
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.main import get_db
from src.engine.photo_engine import photo_engine, ALLOWED_MIME, MAX_FILE_SIZE

router = APIRouter(prefix="/api/v2/photo", tags=["photo"])


# ── 请求模型 ──

class ChatRequest(BaseModel):
    user_id: str
    message: str


# ── 端点 ──

@router.post("/upload")
async def upload_photo(
    file: UploadFile,
    user_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """上传图片 + AI 理解（中英双语描述 + 关键词提取）"""
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少 user_id")

    # 验证文件类型
    mime = file.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {mime}。支持: {', '.join(ALLOWED_MIME)}",
        )

    # 读取文件
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大 ({len(file_bytes)} bytes)，上限 {MAX_FILE_SIZE} bytes",
        )

    filename = file.filename or "photo.jpg"

    try:
        result = await photo_engine.upload_and_understand(
            user_id=user_id,
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime,
            db=db,
        )
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")


@router.post("/{photo_id}/chat")
async def chat_about_photo(
    photo_id: str,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """基于图片的对话"""
    try:
        result = await photo_engine.chat_about_photo(
            photo_id=photo_id,
            user_id=req.user_id,
            message=req.message,
            db=db,
        )
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"图片对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_photo_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取用户的图片历史列表"""
    photos = await photo_engine.get_photo_history(
        user_id=user_id,
        db=db,
        limit=limit,
        offset=offset,
    )
    return {"status": "ok", "data": photos}


@router.get("/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    photo_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取缩略图"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    thumb_path = result.get("thumbnail_path", "")
    if not thumb_path or not os.path.exists(thumb_path):
        # 无缩略图则返回原图
        image_path = result.get("image_path", "")
        if image_path and os.path.exists(image_path):
            return FileResponse(image_path)
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(thumb_path)


@router.get("/{photo_id}/image")
async def get_photo_image(
    photo_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取图片文件"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    image_path = result.get("image_path", "")
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(image_path)


@router.get("/{photo_id}")
async def get_photo_detail(
    photo_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取图片详情（含AI描述、关键词、场景标签）"""
    result = await photo_engine.get_photo_detail(photo_id=photo_id, user_id=user_id, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="图片不存在")
    return {"status": "ok", "data": result}


@router.get("/{photo_id}/chats")
async def get_photo_chats(
    photo_id: str,
    user_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取图片对话历史"""
    try:
        chats = await photo_engine.get_photo_chat_history(
            photo_id=photo_id,
            user_id=user_id,
            db=db,
            limit=limit,
        )
        return {"status": "ok", "data": chats}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
