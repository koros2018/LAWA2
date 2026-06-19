"""
LAWA2 — 提醒 Agent 入口路由 (/agent/reminder)
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Query, Path, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.engine.reminder_engine import reminder_engine
from src.database.main import get_db
from src.middleware.auth import get_current_user_id

router = APIRouter(prefix="/agent/reminder", tags=["reminder-agent"])


class EventCreate(BaseModel):
    title: str
    title_en: Optional[str] = None
    event_date: str
    event_type: str = "personal"
    note: Optional[str] = None
    note_en: Optional[str] = None
    is_recurring: bool = False
    recurring_rule: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    event_date: Optional[str] = None
    event_type: Optional[str] = None
    note: Optional[str] = None
    note_en: Optional[str] = None
    is_done: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurring_rule: Optional[str] = None


# 认证依赖统一从 src.middleware.auth 导入


@router.get("/health")
async def reminder_agent_health():
    """提醒 Agent 健康检查 · Reminder Agent Health Check"""
    return {"status": "ok", "agent": "reminder", "version": "2.5.0"}


@router.get("/events")
async def list_events(
    user_id: str = Depends(get_current_user_id),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    event_type: Optional[str] = Query(None, description="事件类型: personal/holiday/todo/anniversary"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取提醒列表 · Get reminders"""
    events = await reminder_engine.get_events(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        limit=limit,
        db=db,
    )
    return {"status": "ok", "data": events}


@router.get("/events/{event_id}")
async def get_event(
    event_id: str = Path(..., description="事件ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取单个提醒 · Get reminder"""
    event = await reminder_engine.get_event(event_id, user_id, db)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"status": "ok", "data": event}


@router.post("/events")
async def create_event(
    event: EventCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建提醒 · Create reminder"""
    result = await reminder_engine.create_event(
        user_id=user_id,
        title=event.title,
        title_en=event.title_en,
        event_date=event.event_date,
        event_type=event.event_type,
        note=event.note,
        note_en=event.note_en,
        is_recurring=event.is_recurring,
        recurring_rule=event.recurring_rule,
        db=db,
    )
    return {"status": "ok", "data": result}


@router.put("/events/{event_id}")
async def update_event(
    event: EventUpdate,
    event_id: str = Path(..., description="事件ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新提醒 · Update reminder"""
    result = await reminder_engine.update_event(
        event_id=event_id,
        user_id=user_id,
        title=event.title,
        title_en=event.title_en,
        event_date=event.event_date,
        event_type=event.event_type,
        note=event.note,
        note_en=event.note_en,
        is_done=event.is_done,
        is_recurring=event.is_recurring,
        recurring_rule=event.recurring_rule,
        db=db,
    )
    if not result:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"status": "ok", "data": result}


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str = Path(..., description="事件ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除提醒 · Delete reminder"""
    result = await reminder_engine.delete_event(event_id, user_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"status": "ok"}


@router.get("/holidays")
async def get_holidays(
    year: Optional[int] = Query(None, description="年份，默认当前年"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取节假日种子 · Get holiday seeds"""
    holidays = await reminder_engine.seed_holidays(year, db)
    return {"status": "ok", "data": holidays}


@router.get("/holidays/today")
async def get_today_holidays(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取今日节假日 · Get today's holidays"""
    holidays = await reminder_engine.get_holidays_for_today(db)
    return {"status": "ok", "data": holidays}


@router.post("/generate-greeting")
async def generate_greeting(
    event_id: str = Query(..., description="事件ID"),
    user_name: str = Query("你", description="用户姓名"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """为纪念日生成祝福语 · Generate greeting for anniversary"""
    greeting = await reminder_engine.generate_greeting(event_id, user_name)
    if not greeting:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"status": "ok", "data": greeting}
