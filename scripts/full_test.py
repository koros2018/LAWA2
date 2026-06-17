#!/usr/bin/env python3
"""
LAWA2 全面功能测试脚本 v4 - 最终修复版
"""

import requests
import json

BASE_URL = "http://localhost:6290"
USER_ID = "test_user_full_test"

results = []

def assert_status(path: str, expected: int, method: str = "GET", json: dict = None, params: dict = None):
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, json=json, params=params, timeout=10)
    if resp.status_code != expected:
        raise Exception(f"Expected {expected}, got {resp.status_code}: {resp.text[:200]}")
    return resp.json()

def test(name: str, fn):
    try:
        fn()
        results.append(("✅", name))
        print(f"✅ {name}")
    except Exception as e:
        results.append(("❌", f"{name}: {e}"))
        print(f"❌ {name}: {e}")

# ── 1. 健康检查 ──
print("\n📋 1. 健康检查")
test("后端健康检查", lambda: assert_status("/health", 200))

# ── 2. 认证系统 ──
print("\n📋 2. 认证系统")
test("免密码登录", lambda: assert_status("/api/v2/auth/login", 200, method="POST", json={"username": USER_ID}))

# ── 3. 主 Agent ──
print("\n📋 3. 主 Agent (习惯/花园/桥梁)")
test("获取语伴", lambda: assert_status("/api/v2/bridge/partner", 200, params={"user_id": USER_ID}))
test("桥梁进度", lambda: assert_status("/api/v2/bridge/progress", 200, params={"user_id": USER_ID}))
test("花园报告", lambda: assert_status("/api/v1/habit/garden/report", 200, params={"user_id": USER_ID}))
test("成长洞察", lambda: assert_status("/api/v1/habit/garden/growth", 200, params={"user_id": USER_ID}))
test("社交场景语料", lambda: assert_status("/api/v1/habit/social/scene", 200, params={"user_id": USER_ID}))
test("桥梁问候", lambda: assert_status("/api/v2/bridge/greeting", 200, params={"user_id": USER_ID}))
test("桥梁点赞", lambda: assert_status("/api/v2/bridge/like", 200, params={"user_id": USER_ID}))
test("桥梁教梗", lambda: assert_status("/api/v2/bridge/teach", 200, params={"user_id": USER_ID}))
test("桥梁群聊", lambda: assert_status("/api/v2/bridge/group", 200, params={"user_id": USER_ID}))
test("桥梁线下", lambda: assert_status("/api/v2/bridge/offline", 200, params={"user_id": USER_ID}))
test("桥梁历史", lambda: assert_status("/api/v2/bridge/history", 200, params={"user_id": USER_ID}))

# ── 4. 提醒 Agent ──
print("\n📋 4. 提醒 Agent")
test("节假日列表", lambda: assert_status("/api/v2/reminder/holidays", 200))
test("获取事件", lambda: assert_status("/api/v2/reminder/events", 200, params={"user_id": USER_ID}))
test("生成问候", lambda: assert_status("/api/v2/reminder/generate-greeting", 200, method="POST", params={"event_id": "test_event", "user_name": "Test"}))

# ── 5. 拍照 Agent ──
print("\n📋 5. 拍照 Agent")
test("获取图片列表", lambda: assert_status("/api/v2/photo/list", 200, params={"user_id": USER_ID}))

# ── 6. 管理 Agent ──
print("\n📋 6. 管理 Agent")
test("系统统计", lambda: assert_status("/api/v2/admin/stats", 200, params={"admin_user_id": "boss_ke"}))
test("用户列表", lambda: assert_status("/api/v2/admin/users", 200, params={"admin_user_id": "boss_ke", "limit": 10}))

# ── 7. 种子语料 ──
print("\n📋 7. 种子语料管理")
test("获取语料列表", lambda: assert_status("/api/v2/seed/contents", 200, params={"user_id": USER_ID, "page": 1, "page_size": 20}))
test("获取系统语料", lambda: assert_status("/api/v2/seed/contents/system/social_scene", 200))

# ── 8. 日志系统 ──
print("\n📋 8. 日志系统")
test("获取日志", lambda: assert_status("/api/v2/logs", 200, params={"lines": 100}))
test("日志统计", lambda: assert_status("/api/v2/logs/stats", 200))

# ── 9. 错误监控 ──
print("\n📋 9. 错误监控")
test("错误统计", lambda: assert_status("/api/v2/errors/stats", 200))

# ── 10. 推送通知 ──
print("\n📋 10. 推送通知")
test("推送偏好", lambda: assert_status("/api/v2/push/preferences", 200, params={"user_id": USER_ID}))
test("获取通知", lambda: assert_status("/api/v2/push/notifications", 200, params={"user_id": USER_ID}))

# ── 11. Agent 路由 ──
print("\n📋 11. Agent 路由")
test("主 Agent 健康", lambda: assert_status("/agent/main/health", 200))
test("提醒 Agent 健康", lambda: assert_status("/agent/reminder/health", 200))
test("拍照 Agent 健康", lambda: assert_status("/agent/photo/health", 200))

# ── 汇总 ──
print("\n" + "="*50)
print("📊 测试汇总")
print("="*50)
passed = sum(1 for r in results if r[0] == "✅")
failed = sum(1 for r in results if r[0] == "❌")
print(f"总计: {len(results)} 项测试")
print(f"通过: {passed} ✅")
print(f"失败: {failed} ❌")
if failed > 0:
    print("\n失败详情:")
    for status, name in results:
        if status == "❌":
            print(f"  {status} {name}")
else:
    print("\n🎉 全部通过！")
