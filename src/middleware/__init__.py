"""
LAWA2 — 认证模块统一入口

所有认证相关的依赖注入函数统一从 src.middleware.auth 导出。
此文件作为向后兼容的入口，新代码应直接导入 src.middleware.auth。
"""

from src.middleware.auth import (
    bearer_scheme,
    get_current_user_id,
    get_optional_user_id,
    get_current_user,
    require_admin,
)

__all__ = [
    "bearer_scheme",
    "get_current_user_id",
    "get_optional_user_id",
    "get_current_user",
    "require_admin",
]
