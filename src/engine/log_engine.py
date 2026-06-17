"""
LAWA2 — 日志管理引擎

读取和过滤系统日志（基于 loguru 的 sink 输出）。
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
import re


class LogEngine:
    """日志管理引擎"""

    # 日志文件路径（loguru 默认输出到文件）
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / "lawa2.log"

    @staticmethod
    def ensure_log_dir():
        """确保日志目录存在"""
        LogEngine.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def setup_logger():
        """配置 loguru 输出到文件"""
        LogEngine.ensure_log_dir()

        # 移除默认 sink
        logger.remove()

        # 输出到文件（JSON 格式）
        logger.add(
            str(LogEngine.LOG_FILE),
            rotation="500 MB",
            retention="30 days",
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            enqueue=True,
            level="DEBUG",
        )

        # 输出到控制台
        logger.add(
            sink=lambda msg: print(msg, end=""),
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
        )

    @staticmethod
    def read_logs(
        lines: int = 100,
        level: Optional[str] = None,
        search: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict]:
        """读取日志"""
        if not LogEngine.LOG_FILE.exists():
            return []

        logs = []
        pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+) \| (.+?) \| (.+)"
        )

        with open(LogEngine.LOG_FILE, "r", encoding="utf-8") as f:
            # 从文件末尾读取指定行数
            all_lines = f.readlines()[-lines:]

        for line in all_lines:
            match = pattern.match(line.strip())
            if not match:
                continue

            timestamp_str, log_level, location, message = match.groups()

            # 时间过滤
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                continue

            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue

            # 级别过滤
            if level and log_level.upper() != level.upper():
                continue

            # 搜索过滤
            if search and search.lower() not in message.lower():
                continue

            logs.append({
                "timestamp": timestamp.isoformat(),
                "level": log_level,
                "location": location,
                "message": message,
            })

        return logs

    @staticmethod
    def get_log_stats() -> dict:
        """获取日志统计"""
        if not LogEngine.LOG_FILE.exists():
            return {"file_size": 0, "line_count": 0, "last_modified": None}

        stat = LogEngine.LOG_FILE.stat()
        line_count = sum(1 for _ in open(LogEngine.LOG_FILE, "r", encoding="utf-8"))

        return {
            "file_size": stat.st_size,
            "file_size_human": LogEngine._format_size(stat.st_size),
            "line_count": line_count,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @staticmethod
    def clear_logs():
        """清空日志文件"""
        if LogEngine.LOG_FILE.exists():
            LogEngine.LOG_FILE.write_text("")
