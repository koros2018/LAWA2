"""
LAWA2 — 错误监控中间件

全局异常处理 + 错误日志记录 + 错误统计。
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from datetime import datetime
from collections import defaultdict
import traceback
import json


class ErrorStats:
    """错误统计"""
    
    def __init__(self):
        self.errors: dict[str, dict] = defaultdict(lambda: {
            "count": 0,
            "last_occurred": None,
            "sample_message": None,
        })
    
    def record(self, error_type: str, message: str, endpoint: str = ""):
        """记录错误"""
        entry = self.errors[error_type]
        entry["count"] += 1
        entry["last_occurred"] = datetime.utcnow().isoformat()
        if not entry["sample_message"]:
            entry["sample_message"] = message[:200]
    
    def get_top_errors(self, limit: int = 10) -> list[dict]:
        """获取 Top 错误"""
        sorted_errors = sorted(
            self.errors.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:limit]
        return [
            {"error_type": k, **v}
            for k, v in sorted_errors
        ]
    
    def clear(self):
        """清空统计"""
        self.errors.clear()


# 全局错误统计实例
error_stats = ErrorStats()


class ErrorMonitorMiddleware(BaseHTTPMiddleware):
    """错误监控中间件"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # 记录错误
            error_type = type(e).__name__
            error_msg = str(e)
            endpoint = f"{request.method} {request.url.path}"
            
            error_stats.record(error_type, error_msg, endpoint)
            
            # 记录到日志
            logger.exception(f"❌ {endpoint} - {error_type}: {error_msg}")
            
            # 返回友好错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": error_type,
                    "message": "服务器内部错误 · Internal server error",
                    "endpoint": endpoint,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )


class GlobalExceptionHandler:
    """全局异常处理器"""
    
    @staticmethod
    async def handle(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # 记录完整堆栈
            stack_trace = traceback.format_exc()
            
            logger.error(f"🔥 未捕获异常 · Uncaught Exception")
            logger.error(f"   类型: {type(e).__name__}")
            logger.error(f"   消息: {str(e)}")
            logger.error(f"   路径: {request.url.path}")
            logger.error(f"   方法: {request.method}")
            logger.error(f"   堆栈:\n{stack_trace}")
            
            # 记录到错误统计
            error_stats.record(
                type(e).__name__,
                str(e),
                f"{request.method} {request.url.path}"
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": type(e).__name__,
                    "message": "服务器内部错误 · Internal server error",
                    "endpoint": f"{request.method} {request.url.path}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )


def get_error_stats() -> dict:
    """获取错误统计"""
    return {
        "total_unique_errors": len(error_stats.errors),
        "top_errors": error_stats.get_top_errors(10),
        "total_errors": sum(e["count"] for e in error_stats.errors.values()),
    }


def clear_error_stats():
    """清空错误统计"""
    error_stats.clear()
