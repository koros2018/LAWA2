"""
LAWA2 — 日志管理路由

查看系统日志、统计信息、清空日志（仅管理员）。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.database.main import get_db
from src.models.user import User
from src.engine.log_engine import LogEngine
from src.middleware.auth import get_current_user
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api/v2/logs", tags=["logs"])


# ── Request/Response Models ──

class LogEntry(BaseModel):
    timestamp: str
    level: str
    location: str
    message: str


class LogListResponse(BaseModel):
    logs: list[LogEntry]
    total: int


class LogStatsResponse(BaseModel):
    file_size: int
    file_size_human: str
    line_count: int
    last_modified: Optional[str]


class ClearLogsResponse(BaseModel):
    message: str
    cleared: bool


# ── Routes ──

@router.get("", response_model=LogListResponse)
def list_logs(
    current_user: User = Depends(get_current_user),
    lines: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
):
    """列出系统日志"""
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None

    logs = LogEngine.read_logs(
        lines=lines,
        level=level,
        search=search,
        start_time=start_dt,
        end_time=end_dt,
    )

    return LogListResponse(
        logs=[LogEntry(**log) for log in logs],
        total=len(logs),
    )


@router.get("/stats", response_model=LogStatsResponse)
def get_log_stats(
    current_user: User = Depends(get_current_user),
):
    """获取日志统计信息"""
    stats = LogEngine.get_log_stats()
    # Ensure file_size_human is always present
    if 'file_size_human' not in stats:
        stats['file_size_human'] = LogEngine._format_size(stats.get('file_size', 0))
    return LogStatsResponse(**stats)


@router.delete("", response_model=ClearLogsResponse)
async def clear_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """清空日志文件（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限 · Admin access required")

    LogEngine.clear_logs()
    return ClearLogsResponse(message="日志已清空 · Logs cleared ✓", cleared=True)
