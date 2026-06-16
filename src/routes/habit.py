"""
LAWA 习惯引擎 — API 路由

提供：
  - POST /api/v1/habit/action      — 记录微行为
  - GET  /api/v1/habit/summary     — 今日行为摘要
  - GET  /api/v1/habit/habits      — 可用行为列表
  - GET  /api/v1/habit/feed        — 获取信息流
  - GET  /api/v1/habit/rewards     — 最近奖励
  - POST /api/v1/habit/config      — 更新配置
  - GET  /api/v1/habit/garden      — 花园状态
  - GET  /api/v1/habit/milestones  — 里程碑
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from src.engine.action_engine import ActionEngine
from src.engine.reward_engine import RewardEngine
from src.engine.trigger_engine import TriggerEngine
from src.engine.investment_engine import InvestmentEngine

router = APIRouter(prefix="/api/v1/habit", tags=["habit"])


# ── 依赖注入 ──

def get_action_engine() -> ActionEngine:
    return ActionEngine()

def get_reward_engine() -> RewardEngine:
    return RewardEngine()

def get_trigger_engine() -> TriggerEngine:
    return TriggerEngine()

def get_investment_engine() -> InvestmentEngine:
    return InvestmentEngine()

async def get_current_user_id(user_id: str = "default_user") -> str:
    """从请求参数获取 user_id"""
    return user_id


# ── 请求/响应模型 ──

class RecordActionRequest(BaseModel):
    habit_code: str = Field(..., description="行为类型")
    duration_seconds: int = Field(0, description="耗时（秒）")
    completion_status: str = Field("completed", description="完成状态")
    triggered_by: str = Field("manual", description="触发方式")
    feed_id: Optional[str] = Field(None, description="关联信息流")

class UpdateComprehensionRequest(BaseModel):
    feed_id: str
    score: float = Field(..., ge=0, le=1)
    duration_seconds: int

class UpdateConfigRequest(BaseModel):
    trigger_time_slot: Optional[str] = None
    info_source_prefs: Optional[list[str]] = None
    action_prefs: Optional[list[str]] = None
    reward_frequency: Optional[str] = None
    feed_enabled: Optional[bool] = None
    morning_time: Optional[str] = None
    noon_time: Optional[str] = None
    evening_time: Optional[str] = None


class UpdateSocialLevelRequest(BaseModel):
    vocab_id: str
    new_level: str  # understand|use|create


# ── 路由 ──

@router.post("/action")
async def record_action(
    req: RecordActionRequest,
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
):
    """记录一个微行为"""
    try:
        result = await engine.record_habit(
            user_id=user_id,
            habit_code=req.habit_code,
            duration_seconds=req.duration_seconds,
            completion_status=req.completion_status,
            triggered_by=req.triggered_by,
            feed_id=req.feed_id,
        )
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary")
async def get_summary(
    engine: ActionEngine = Depends(get_action_engine),
    user_id: str = Depends(get_current_user_id),
):
    """今日行为摘要"""
    result = await engine.get_today_summary(user_id)
    return {"status": "ok", "data": result}


@router.get("/habits")
async def list_habits(
    engine: ActionEngine = Depends(get_action_engine),
):
    """列出所有可用行为类型"""
    return {"status": "ok", "data": engine.list_available_habits()}


@router.get("/feed")
async def get_feed(
    time_slot: str = "morning",
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取一条信息流内容"""
    result = await engine.get_feed(user_id, time_slot)
    return {"status": "ok", "data": result}


@router.get("/feeds")
async def list_feeds(
    limit: int = 10,
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取最近的信息流"""
    result = await engine.get_recent_feeds(user_id, limit)
    return {"status": "ok", "data": result}


@router.post("/feed/comprehension")
async def update_comprehension(
    req: UpdateComprehensionRequest,
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """更新信息流理解度评分"""
    ok = await engine.update_comprehension(user_id, req.feed_id, req.score, req.duration_seconds)
    if not ok:
        raise HTTPException(status_code=404, detail="Feed not found")
    return {"status": "ok"}


@router.get("/rewards")
async def list_rewards(
    limit: int = 10,
    engine: RewardEngine = Depends(get_reward_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取最近的可变奖励"""
    result = await engine.get_recent_rewards(user_id, limit)
    return {"status": "ok", "data": result}


@router.get("/config")
async def get_config(
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取用户习惯配置"""
    config = await engine.get_user_config(user_id)
    return {"status": "ok", "data": config}


@router.post("/config")
async def update_config(
    req: UpdateConfigRequest,
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """更新用户习惯配置"""
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    result = await engine.update_user_config(user_id, updates)
    return {"status": "ok", "data": result}


@router.get("/garden")
async def get_garden(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取语言花园状态"""
    garden = await engine.get_garden_status(user_id)
    milestones = await engine.check_milestones(user_id)
    return {
        "status": "ok",
        "data": {
            "garden": garden,
            "new_milestones": milestones,
        },
    }


# ── 社交场景路由 ──

@router.get("/social/scene")
async def get_social_scene(
    category: str = "net_slang",
    lang_direction: str = "zh",
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取一条社交场景内容"""
    result = await engine.get_social_scene(user_id, lang_direction, category)
    return {"status": "ok", "data": result}


@router.get("/social/adaptive")
async def get_adaptive_scene(
    lang_direction: str = "zh",
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """根据用户社交理解度获取合适场景"""
    result = await engine.get_social_scene_by_level(user_id, lang_direction)
    return {"status": "ok", "data": result}


@router.post("/social/level")
async def update_social_level(
    req: UpdateSocialLevelRequest,
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """更新社交词汇理解等级"""
    ok = await engine.update_social_understanding(
        user_id, req.vocab_id, req.new_level
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Vocab not found")
    return {"status": "ok"}


@router.get("/social/progress")
async def get_social_progress(
    engine: TriggerEngine = Depends(get_trigger_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取社交学习进度"""
    result = await engine.get_social_progress(user_id)
    return {"status": "ok", "data": result}


@router.get("/milestones")
async def list_milestones(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取所有里程碑"""
    result = await engine.get_milestones(user_id)
    return {"status": "ok", "data": result}


@router.post("/asset")
async def add_asset(
    asset_type: str,
    asset_data: dict,
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """添加一条语言资产"""
    result = await engine.add_asset(user_id, asset_type, asset_data)
    return {"status": "ok", "data": result}


@router.get("/assets")
async def list_assets(
    asset_type: Optional[str] = None,
    limit: int = 20,
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取语言资产列表"""
    result = await engine.get_assets(user_id, asset_type, limit)
    return {"status": "ok", "data": result}


@router.get("/garden/vocab-details")
async def get_garden_vocab_details(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取词汇明细（含社交词汇分类统计）"""
    result = await engine.get_vocab_details(user_id)
    return {"status": "ok", "data": result}


@router.get("/garden/growth")
async def get_garden_growth(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取成长曲线数据"""
    result = await engine.get_growth_curve(user_id)
    return {"status": "ok", "data": result}


@router.get("/garden/report")
async def get_garden_report(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取花园周报"""
    result = await engine.get_garden_report(user_id)
    return {"status": "ok", "data": result}


@router.get("/garden/health")
async def get_health_insights(
    engine: InvestmentEngine = Depends(get_investment_engine),
    user_id: str = Depends(get_current_user_id),
):
    """获取习惯健康度洞察"""
    result = await engine.get_health_insights(user_id)
    return {"status": "ok", "data": result}
