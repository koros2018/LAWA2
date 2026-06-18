# 🐛 LAWA2 问题追踪

> 全面功能测试发现的问题，按优先级排序

---

## Phase 6 增补任务

### 6.11 推送路由注册修复 ✅ 已修复

**问题**：`push.py` 中的 health 端点未注册到主应用
- 路径：`/api/v2/push/health`
- 错误：404 Not Found

**修复**：
- 在 `push.py` 中添加 `/health` 端点
- 在 `main.py` 中注册 `push_router`

**状态**: ✅ 已修复

---

### 6.12 Push 模块缺少 Path 导入 ✅ 已修复

**问题**：`push.py` 使用 `Path` 但未导入
- 文件：`src/routes/push.py`
- 错误：`NameError: name 'Path' is not defined`

**修复**：添加 `from fastapi import ..., Path`

**状态**: ✅ 已修复

---

### 6.13 测试用例参数修正 ✅ 已修复

**问题**：测试用例方法/参数错误
- `Habit Feed`：应为 GET 而非 POST
- `Bridge Greeting`：应为 GET 而非 POST
- `Bridge Reply`：缺少 `reply_text` 参数

**修复**：更新 `tests/test_full_function.py`

**状态**: ✅ 已修复

---

### 6.14 Bridge Reply 需要有效 interaction_id

**问题**：测试用例使用无效的 `interaction_id`
- 路径：`/api/v2/bridge/reply`
- 错误：`{"detail": "Interaction not found"}`

**说明**：这是合理的业务错误，说明 API 正常工作。
测试用例需要使用数据库中实际存在的 interaction_id。

**状态**: ⚠️ 测试用例需改进（非代码 bug）

---

## 测试统计

| 指标 | 数量 |
|------|------|
| 总端点数 | 22 |
| 通过 | 21 ✅ |
| 失败（合理错误） | 1 ⚠️ |
| 实际代码 bug | 0 |

---

*最后更新: 2026-06-18*
