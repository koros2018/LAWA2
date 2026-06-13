"""
LAWA 后台任务模块

在 FastAPI lifespan 中启动，定期执行维护操作：
- CompanionSession 超时自动关闭（#7）
- Task deadline 过期自动标记（#8）
- LLM Provider 健康检查 + 告警（#4）
"""
import asyncio
from datetime import datetime, timezone, timedelta
from loguru import logger
from sqlalchemy import text
from src.database.main import AsyncSessionLocal
from src.config import settings
from src.services.llm_service import llm_service


# ── 配置（从 config.py 读取）──
SESSION_TIMEOUT_HOURS = 24       # 超过24小时无活动的会话自动关闭
TASK_DEADLINE_GRACE_HOURS = settings.task_deadline_grace_hours
CHECK_INTERVAL_SECONDS = settings.background_check_interval_seconds

# 健康检查的间隔倍数（每N次维护循环执行一次健康检查）
# 默认 12 → 300s * 12 = 3600s = 每1小时
LLM_HEALTH_CHECK_INTERVAL = 12

# 连续失败告警阈值
LLM_HEALTH_ALERT_THRESHOLD = 3


async def _close_stale_sessions():
    """关闭超时的 CompanionSession（#7）"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=SESSION_TIMEOUT_HOURS)
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        # 使用原生 SQL 避免 ORM 自动加载不存在的列
        result = await db.execute(
            text("""
                SELECT id FROM companion_sessions
                WHERE status = 'active' AND created_at < :cutoff
            """),
            {"cutoff": cutoff},
        )
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return

        await db.execute(
            text("""
                UPDATE companion_sessions
                SET status = 'abandoned', ended_at = :now
                WHERE id IN :ids
            """),
            {"ids": ids, "now": now},
        )
        await db.commit()
        logger.info(
            f"⏰ 自动关闭 {len(ids)} 个超时会话 "
            f"(idle > {SESSION_TIMEOUT_HOURS}h)"
        )


async def _expire_overdue_tasks():
    """将超 deadline 的任务标记为 expired（#8）"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=TASK_DEADLINE_GRACE_HOURS)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT id FROM tasks
                WHERE status = 'open' AND deadline IS NOT NULL AND deadline < :cutoff
            """),
            {"cutoff": cutoff},
        )
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return

        await db.execute(
            text("""
                UPDATE tasks
                SET status = 'expired'
                WHERE id IN :ids
            """),
            {"ids": ids},
        )
        await db.commit()
        logger.info(
            f"⏰ 过期 {len(ids)} 个超 deadline 任务 "
            f"(deadline > {TASK_DEADLINE_GRACE_HOURS}h ago)"
        )


async def _check_llm_health(cycle_count: int):
    """LLM Provider 健康检查 + 告警日志（#4）

    每隔 LLM_HEALTH_CHECK_INTERVAL 次循环执行一次。
    连续失败超过 LLM_HEALTH_ALERT_THRESHOLD 次时升级告警级别。
    """
    if cycle_count % LLM_HEALTH_CHECK_INTERVAL != 0:
        return

    try:
        result = await llm_service.health_check_all()
        if not result["healthy"] or result["healthy_count"] < result["total"]:
            # 有 Provider 不健康 → 告警日志
            unhealthy = [p for p in result["providers"] if not p["healthy"]]
            for p in unhealthy:
                logger.warning(
                    f"⚠️ LLM Provider 不健康: {p['provider']} "
                    f"| error: {p['error']} | latency: {p['latency_ms']}ms"
                )
            logger.warning(
                f"🚨 LLM 健康检查告警: {result['healthy_count']}/{result['total']} 正常 "
                f"| 异常Provider: {[p['provider'] for p in unhealthy]}"
            )
        else:
            latencies = [p["latency_ms"] for p in result["providers"] if p["healthy"]]
            logger.debug(
                f"✅ LLM 全部健康 ({result['total']}/{result['total']}) "
                f"| 延迟: {latencies}ms"
            )
    except Exception as e:
        logger.error(f"❌ LLM 健康检查执行异常: {e}")


async def _maintenance_loop():
    """后台维护循环"""
    _cycle = 0
    logger.info(
        f"🔄 后台任务启动: 会话超时={SESSION_TIMEOUT_HOURS}h "
        f"| 任务过期={TASK_DEADLINE_GRACE_HOURS}h "
        f"| 间隔={CHECK_INTERVAL_SECONDS}s "
        f"| LLM健康检查每{LLM_HEALTH_CHECK_INTERVAL * CHECK_INTERVAL_SECONDS // 60}分钟一次"
    )
    while True:
        _cycle += 1
        try:
            await _close_stale_sessions()
            await _expire_overdue_tasks()
            await _check_llm_health(_cycle)
        except Exception as e:
            logger.error(f"后台维护异常: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def start_background_tasks():
    """在 lifespan 中调用，启动后台任务"""
    task = asyncio.create_task(_maintenance_loop(), name="lawa-bg-maintenance")
    return task
