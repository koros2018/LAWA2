"""
LAWA2 全面功能测试脚本 v2

测试所有主要 API 端点，记录问题。
使用正确的路由路径。
"""

import httpx
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app=app, base_url="http://test")

# 测试结果记录
results = []
issues = []

def test_endpoint(name, method, path, params=None, json=None, files=None, data=None, expected_status=200):
    """测试单个端点"""
    try:
        if method == "GET":
            response = client.get(path, params=params or {})
        elif method == "POST":
            if files:
                response = client.post(path, files=files, data=data or {})
            elif json:
                response = client.post(path, json=json)
            else:
                response = client.post(path, data=data or {})
        elif method == "PUT":
            response = client.put(path, json=json or {})
        elif method == "DELETE":
            response = client.delete(path, params=params or {})
        else:
            return
        
        status_ok = response.status_code == expected_status
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": response.status_code,
            "expected": expected_status,
            "ok": status_ok,
        })
        
        if not status_ok:
            issues.append({
                "name": name,
                "path": path,
                "expected": expected_status,
                "actual": response.status_code,
                "detail": response.text[:200] if response.text else "Empty",
            })
            
    except Exception as e:
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": "ERROR",
            "expected": expected_status,
            "ok": False,
        })
        issues.append({
            "name": name,
            "path": path,
            "error": str(e)[:200],
        })

# ── 健康检查 ──
test_endpoint("Health", "GET", "/health")
test_endpoint("API Health", "GET", "/api/v1/health")

# ── 认证相关 ──
test_endpoint("Auth Login", "POST", "/api/v2/auth/login", json={"username": "test_user"})
test_endpoint("Auth Profile", "POST", "/api/v2/auth/profile", json={"username": "test_user", "display_name": "Test"})

# ── 习惯引擎 (v1) ──
test_endpoint("Habit List", "GET", "/api/v1/habit/habits", params={"user_id": "test_user"})
test_endpoint("Habit Feed", "GET", "/api/v1/habit/feed", params={"user_id": "test_user", "time_slot": "morning"})
test_endpoint("Habit Stats", "GET", "/api/v1/habit/summary", params={"user_id": "test_user"})
test_endpoint("Habit Garden", "GET", "/api/v1/habit/garden", params={"user_id": "test_user"})

# ── 桥梁对话 (v2) ──
test_endpoint("Bridge History", "GET", "/api/v2/bridge/history", params={"user_id": "test_user", "limit": 10})
test_endpoint("Bridge Reply", "POST", "/api/v2/bridge/reply", json={"user_id": "test_user", "interaction_id": "test", "reply_text": "Hello"})
test_endpoint("Bridge Greeting", "GET", "/api/v2/bridge/greeting", params={"user_id": "test_user"})

# ── 提醒 Agent ──
test_endpoint("Reminder Events", "GET", "/api/v2/reminder/events", params={"user_id": "test_user"})
test_endpoint("Reminder Holidays", "GET", "/api/v2/reminder/holidays")
test_endpoint("Reminder Upcoming", "GET", "/api/v2/reminder/upcoming", params={"user_id": "test_user", "days": 7})

# ── 拍照 Agent (v2) ──
test_endpoint("Photo List", "GET", "/api/v2/photo/list", params={"user_id": "test_user", "limit": 10})

# ── 管理员 ──
test_endpoint("Admin Stats", "GET", "/api/v2/admin/stats")

# ── 种子语料 ──
test_endpoint("Seed Contents", "GET", "/api/v2/seed/contents", params={"user_id": "test_user", "limit": 10})
test_endpoint("Seed System", "GET", "/api/v2/seed/contents/system/social_scene")

# ── 日志 ──
test_endpoint("Logs Stats", "GET", "/api/v2/logs/stats")

# ── 错误监控 ──
test_endpoint("Errors Stats", "GET", "/api/v2/errors/stats")

# ── 推送 ──
test_endpoint("Push Health", "GET", "/api/v2/push/health")

# ── 测试用户 ──
test_endpoint("TestUser Health", "GET", "/api/v2/test-users/health")

# ── 打印结果 ──
print("=" * 60)
print("LAWA2 全面功能测试结果")
print("=" * 60)

passed = sum(1 for r in results if r["ok"])
failed = sum(1 for r in results if not r["ok"])

print(f"\n总计: {len(results)} 个端点")
print(f"通过: {passed} ✅")
print(f"失败: {failed} ❌")

if issues:
    print("\n" + "=" * 60)
    print("问题列表:")
    print("=" * 60)
    for issue in issues:
        print(f"\n❌ {issue['name']}")
        print(f"   路径: {issue['path']}")
        print(f"   期望: {issue.get('expected', 'N/A')}")
        print(f"   实际: {issue.get('actual', issue.get('error', 'N/A'))}")
        if "detail" in issue:
            print(f"   详情: {issue['detail'][:100]}")

print("\n" + "=" * 60)
