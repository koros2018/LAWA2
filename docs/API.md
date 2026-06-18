# LAWA2 API 文档

> 版本：v3.8.0 | 更新日期：2026-06-18

---

## 基础信息

- **Base URL**: `http://localhost:6290`
- **API 版本**: `/api/v1`, `/api/v2`
- **认证方式**: Query 参数 `user_id` 或 Bearer Token

---

## 健康检查

### GET /health

系统健康检查

**响应**:
```json
{
  "status": "ok",
  "app": "LAWA2",
  "version": "2.0.0"
}
```

### GET /api/v1/health

API 健康检查（含数据库信息）

**响应**:
```json
{
  "status": "ok",
  "app": "LAWA2",
  "version": "2.0.0",
  "database": "lawa2"
}
```

---

## 习惯引擎 API (v1)

### GET /api/v1/habit/habits

获取用户习惯列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |

**响应**:
```json
{
  "status": "ok",
  "data": [
    {
      "id": "uuid",
      "name": "每日阅读",
      "current_streak": 7,
      "level": 3
    }
  ]
}
```

### GET /api/v1/habit/feed

获取一条信息流内容

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| time_slot | string | 时间段: morning/noon/evening |

### GET /api/v1/habit/summary

获取用户习惯统计

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |

### GET /api/v1/habit/garden

获取用户花园（词汇/表达收集）

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |

---

## 桥梁对话 API (v2)

### GET /api/v2/bridge/history

获取对话历史

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| limit | number | 数量限制 (默认 10) |

### POST /api/v2/bridge/reply

回复对话

**请求体**:
```json
{
  "user_id": "string",
  "interaction_id": "string",
  "reply_text": "string"
}
```

### POST /api/v2/bridge/greeting

获取问候语

**请求体**:
```json
{
  "user_id": "string"
}
```

---

## 事项提醒 API (v2)

### GET /api/v2/reminder/events

获取提醒事件列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| start_date | string | 开始日期 (YYYY-MM-DD) |
| end_date | string | 结束日期 (YYYY-MM-DD) |
| event_type | string | 事件类型 |

### GET /api/v2/reminder/holidays

获取节假日列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| year | number | 年份 (默认当前年) |

### GET /api/v2/reminder/upcoming

获取即将到来的事件

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| days | number | 未来几天 (默认 7) |

---

## 拍照理解 API (v2)

### POST /api/v2/photo/upload

上传图片并获取 AI 理解

**请求**:
- `file`: 图片文件 (JPEG/PNG, < 5MB)
- `user_id`: 用户 ID

**响应**:
```json
{
  "status": "ok",
  "data": {
    "id": "uuid",
    "ai_description": "中文描述",
    "ai_description_en": "English description",
    "extracted_words": [...],
    "scene_tags": [...]
  }
}
```

### GET /api/v2/photo/list

获取图片列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| limit | number | 数量限制 |
| offset | number | 偏移量 |

### GET /api/v2/photo/{photo_id}

获取图片详情

### POST /api/v2/photo/{photo_id}/chat

基于图片对话

**请求体**:
```json
{
  "user_id": "string",
  "message": "string"
}
```

---

## 管理员 API (v2)

### GET /api/v2/admin/stats

获取系统统计（仅管理员）

**响应**:
```json
{
  "status": "ok",
  "data": {
    "user_count": 100,
    "active_users_today": 25,
    "total_habit_events": 500,
    "today_habit_events": 50
  }
}
```

### GET /api/v2/admin/users

获取用户列表（仅管理员）

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 搜索关键词 |
| limit | number | 每页数量 (默认 20) |
| offset | number | 偏移量 |

### POST /api/v2/admin/users/{user_id}/toggle

切换用户激活状态（仅管理员）

### POST /api/v2/admin/users/{user_id}/admin

设置管理员权限（仅管理员）

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| is_admin | boolean | 是否管理员 |

---

## 种子语料 API (v2)

### GET /api/v2/seed/contents

获取种子语料列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |
| content_type | string | 内容类型 |
| is_active | boolean | 是否启用 |
| search | string | 搜索关键词 |
| page | number | 页码 |
| page_size | number | 每页数量 |

### POST /api/v2/seed/contents

创建种子语料

### PUT /api/v2/seed/contents/{id}

更新种子语料

### DELETE /api/v2/seed/contents/{id}

删除种子语料

### GET /api/v2/seed/contents/system/{type}

获取系统内置语料

---

## 日志 API (v2)

### GET /api/v2/logs/stats

获取日志统计

**响应**:
```json
{
  "file_size": 1024,
  "file_size_human": "1 KB",
  "line_count": 100,
  "last_modified": "2026-06-18T12:00:00Z"
}
```

### GET /api/v2/logs

获取日志列表

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| lines | number | 返回条数 |
| level | string | 日志级别 |
| search | string | 搜索关键词 |

### DELETE /api/v2/logs

清空日志（仅管理员）

---

## 错误监控 API (v2)

### GET /api/v2/errors/stats

获取错误统计

**响应**:
```json
{
  "total_unique_errors": 5,
  "total_errors": 20,
  "top_errors": [...]
}
```

### DELETE /api/v2/errors/stats

清空错误统计（仅管理员）

---

## 推送 API (v2)

### GET /api/v2/push/health

推送服务健康检查

### GET /api/v2/push/preferences

获取推送偏好

### PUT /api/v2/push/preferences

更新推送偏好

### GET /api/v2/push/notifications

获取通知列表

### PUT /api/v2/push/notifications/{id}/read

标记通知已读

### POST /api/v2/push/check

手动触发推送检查

### POST /api/v2/push/test

发送测试通知

---

## 测试用户 API (v2)

### GET /api/v2/test-users/health

测试用户服务健康检查

### GET /api/v2/test-users

获取测试用户列表（仅管理员）

### POST /api/v2/test-users

创建测试用户（仅管理员）

### POST /api/v2/test-users/default

创建默认测试用户集合（仅管理员）

### GET /api/v2/test-users/{username}

获取测试用户详情（仅管理员）

### DELETE /api/v2/test-users/{username}

删除测试用户（仅管理员）

### POST /api/v2/test-users/{username}/reset

重置测试用户（仅管理员）

### DELETE /api/v2/test-users

清理测试用户（仅管理员）

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

*文档维护：Ke & 达子 | 2026-06-18*
