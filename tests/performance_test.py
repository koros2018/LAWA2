"""
LAWA2 性能测试脚本

测试主要 API 端点的响应时间，识别性能瓶颈。
"""

import time
import httpx
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app=app, base_url="http://test")

# 性能测试结果
results = []

def measure_endpoint(name, method, path, params=None, json=None, iterations=5):
    """测量端点响应时间"""
    times = []
    
    for i in range(iterations):
        start = time.time()
        
        if method == "GET":
            response = client.get(path, params=params or {})
        elif method == "POST":
            response = client.post(path, json=json or {})
        else:
            continue
        
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)
        
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": response.status_code,
            "response_time_ms": round(elapsed, 2),
            "iteration": i + 1,
        })
    
    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)
    
    return {
        "name": name,
        "avg_ms": round(avg, 2),
        "min_ms": round(min_t, 2),
        "max_ms": round(max_t, 2),
        "status": "OK" if avg < 500 else "SLOW" if avg < 1000 else "CRITICAL",
    }

# ── 测试主要端点 ──

print("=" * 60)
print("LAWA2 性能测试")
print("=" * 60)

# 健康检查
measure_endpoint("Health", "GET", "/health")
measure_endpoint("API Health", "GET", "/api/v1/health")

# 习惯引擎
measure_endpoint("Habit List", "GET", "/api/v1/habit/habits", {"user_id": "test_user"})
measure_endpoint("Habit Feed", "GET", "/api/v1/habit/feed", {"user_id": "test_user", "time_slot": "morning"})
measure_endpoint("Habit Stats", "GET", "/api/v1/habit/summary", {"user_id": "test_user"})

# 桥梁对话
measure_endpoint("Bridge History", "GET", "/api/v2/bridge/history", {"user_id": "test_user", "limit": 10})

# 提醒 Agent
measure_endpoint("Reminder Events", "GET", "/api/v2/reminder/events", {"user_id": "test_user"})
measure_endpoint("Reminder Holidays", "GET", "/api/v2/reminder/holidays")

# 拍照 Agent
measure_endpoint("Photo List", "GET", "/api/v2/photo/list", {"user_id": "test_user", "limit": 10})

# 种子语料
measure_endpoint("Seed Contents", "GET", "/api/v2/seed/contents", {"user_id": "test_user", "limit": 10})

# 管理员
measure_endpoint("Admin Stats", "GET", "/api/v2/admin/stats")

# 日志
measure_endpoint("Logs Stats", "GET", "/api/v2/logs/stats")

# 错误监控
measure_endpoint("Errors Stats", "GET", "/api/v2/errors/stats")

# ── 打印结果 ──

print("\n" + "=" * 60)
print("性能测试结果（平均响应时间）")
print("=" * 60)

# 按平均响应时间排序
summary = {}
for r in results:
    key = r["name"]
    if key not in summary:
        summary[key] = {"times": [], "status": r["status"]}
    summary[key]["times"].append(r["response_time_ms"])

for name, data in sorted(summary.items(), key=lambda x: sum(x[1]["times"])/len(x[1]["times"])):
    avg = sum(data["times"]) / len(data["times"])
    min_t = min(data["times"])
    max_t = max(data["times"])
    status = "✅" if avg < 200 else "⚠️" if avg < 500 else "🔴"
    print(f"{status} {name:25} avg: {avg:6.1f}ms  min: {min_t:6.1f}ms  max: {max_t:6.1f}ms")

print("\n" + "=" * 60)
print("性能目标:")
print("  ✅ < 200ms  - 优秀")
print("  ⚠️ 200-500ms - 良好")
print("  🔴 > 500ms  - 需要优化")
print("=" * 60)
