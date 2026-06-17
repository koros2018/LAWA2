"""
LAWA2 — 错误监控 API

查看错误统计、Top 错误、清空统计（仅管理员）。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.middleware.error_monitor import get_error_stats, clear_error_stats
from src.middleware.auth_middleware import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2/errors", tags=["errors"])


# ── Response Models ──

class ErrorEntry(BaseModel):
    error_type: str
    count: int
    last_occurred: str | None
    sample_message: str | None


class ErrorStatsResponse(BaseModel):
    total_unique_errors: int
    total_errors: int
    top_errors: list[ErrorEntry]


# ── Routes ──

@router.get("/stats", response_model=ErrorStatsResponse)
def get_errors_stats(
    current_user: User = Depends(get_current_user),
):
    """获取错误统计"""
    stats = get_error_stats()
    return ErrorStatsResponse(**stats)


@router.delete("/stats")
def clear_errors_stats(
    current_user: User = Depends(get_current_user),
):
    """清空错误统计（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限 · Admin access required")
    clear_error_stats()
    return {"message": "错误统计已清空 · Stats cleared ✓"}
