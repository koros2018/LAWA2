# LAWA2 v5.0.0 规划文档

**版本**: v5.0.0  
**主题**: 新功能大版本 — AI 对话增强 + 社交功能  
**预计发布**: 2026 年 7 月中旬  
**状态**: 规划中

---

## 一、版本目标

在 v4.x 打磨轮（稳定性、PWA、错误处理）完成的基础上，v5.0.0 聚焦**功能扩展**：

1. **AI 对话增强** — 更智能的语伴互动
2. **社交功能** — 用户间互动与分享
3. **数据可视化** — 成长曲线与洞察
4. **移动端优化** — PWA 深度集成

---

## 二、功能模块

### 2.1 AI 对话增强 (Agent: main)

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **智能纠错** | 用户输入后，AI 自动纠正语法/用词错误 | P0 |
| **语境扩展** | 根据对话内容，AI 主动拓展相关话题 | P0 |
| **多轮记忆** | AI 记住上下文，支持连续对话 | P0 |
| **语音输入** | 支持语音转文字输入 | P1 |
| **语音输出** | AI 语音回复（TTS） | P1 |
| **对话模式切换** | 自由对话 / 主题对话 / 考试模拟 | P1 |

**技术实现**:
- 后端: `src/services/conversation.py` — 对话状态管理
- 前端: `src/views/ConversationPage.vue` — 对话界面
- API: `/api/v2/conversation/*`

### 2.2 社交功能 (Agent: social)

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **语伴匹配** | 根据水平/兴趣匹配语伴 | P0 |
| **群组学习** | 创建/加入学习群组 | P0 |
| **动态分享** | 分享学习成就/心得 | P1 |
| **点赞评论** | 对动态进行互动 | P1 |
| **排行榜** | 学习时长/XP 排名 | P2 |

**技术实现**:
- 后端: `src/services/social.py` — 社交服务
- 前端: `src/views/SocialPage.vue` — 社交首页
- API: `/api/v2/social/*`

### 2.3 数据可视化 (Agent: analytics)

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **成长曲线** | 词汇量/XP/等级随时间变化 | P0 |
| **学习热力图** | 每日学习强度可视化 | P0 |
| **词云图** | 高频词汇可视化 | P1 |
| **对比分析** | 与同龄人/平均水平对比 | P1 |
| **导出报告** | 生成 PDF/CSV 学习报告 | P2 |

**技术实现**:
- 前端: `src/views/AnalyticsPage.vue` — 数据看板
- 图表: ECharts 5.x (已集成)
- API: `/api/v2/analytics/*`

### 2.4 移动端优化 (PWA 深度集成)

| 功能 | 描述 | 优先级 |
|------|------|--------|
| **离线对话** | 无网络时缓存对话记录 | P0 |
| **推送通知** | 学习提醒/语伴消息推送 | P0 |
| **桌面图标** | 添加到主屏幕 | P0 (已支持) |
| **全屏模式** | 隐藏浏览器 UI | P1 |
| **手势操作** | 滑动切换/下拉刷新 | P1 |
| **相机集成** | 拍照识别 + 语音输入 | P1 |

---

## 三、技术架构

### 3.1 后端新增模块

```
src/
├── services/
│   ├── conversation.py    # 对话服务
│   ├── social.py          # 社交服务
│   └── analytics.py       # 数据分析服务
├── models/
│   ├── conversation.py    # 对话模型
│   ├── social.py          # 社交模型
│   └── analytics.py       # 分析模型
├── routes/
│   ├── conversation.py    # 对话路由
│   ├── social.py          # 社交路由
│   └── analytics.py       # 分析路由
```

### 3.2 前端新增页面

```
frontend/src/views/
├── ConversationPage.vue   # 对话页面
├── SocialPage.vue         # 社交页面
├── AnalyticsPage.vue      # 数据看板
└── components/
    ├── ChatBubble.vue     # 对话气泡
    ├── MatchCard.vue      # 语伴匹配卡片
    ├── Heatmap.vue        # 热力图组件
    └── WordCloud.vue      # 词云组件
```

### 3.3 数据库新增表

```sql
-- 对话记录
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    partner_id INTEGER,
    topic TEXT,
    messages JSON,  -- 对话消息列表
    created_at DATETIME,
    updated_at DATETIME
);

-- 语伴关系
CREATE TABLE partnerships (
    id INTEGER PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    status TEXT,  -- pending/active/blocked
    created_at DATETIME
);

-- 群组
CREATE TABLE groups (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    creator_id INTEGER NOT NULL,
    member_count INTEGER DEFAULT 0,
    created_at DATETIME
);

-- 动态
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content TEXT,
    media_url TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    created_at DATETIME
);

-- 学习记录（用于分析）
CREATE TABLE learning_records (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    actions INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    words_learned INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);
```

---

## 四、开发计划

### Phase 1: AI 对话增强 (2 周)

| Sprint | 内容 | 交付 |
|--------|------|------|
| S1 | 对话服务 + 多轮记忆 | `services/conversation.py` |
| S2 | 智能纠错 + 语境扩展 | `/api/v2/conversation/*` |
| S3 | 对话页面 + 界面 | `ConversationPage.vue` |
| S4 | 语音输入/输出集成 | TTS + STT SDK |

### Phase 2: 社交功能 (2 周)

| Sprint | 内容 | 交付 |
|--------|------|------|
| S5 | 语伴匹配算法 | `services/social.py` |
| S6 | 群组 + 动态 | `/api/v2/social/*` |
| S7 | 社交页面 + 界面 | `SocialPage.vue` |
| S8 | 点赞评论 + 通知 | 推送服务集成 |

### Phase 3: 数据可视化 (1 周)

| Sprint | 内容 | 交付 |
|--------|------|------|
| S9 | 成长曲线 + 热力图 | `AnalyticsPage.vue` |
| S10 | 词云 + 对比分析 | ECharts 组件 |

### Phase 4: 测试与发布 (1 周)

| Sprint | 内容 | 交付 |
|--------|------|------|
| S11 | 集成测试 + 性能优化 | 全链路测试 |
| S12 | 灰度发布 + 监控 | 生产部署 |

---

## 五、依赖与风险

### 5.1 外部依赖

| 依赖 | 用途 | 状态 |
|------|------|------|
| **DeepSeek API** | AI 对话生成 | ✅ 已配置 |
| **ElevenLabs TTS** | 语音输出 | ⏳ 需申请 |
| **Web Speech API** | 语音输入 | ✅ 浏览器原生 |
| **Firebase Cloud Messaging** | 推送通知 | ⏳ 需配置 |

### 5.2 技术风险

| 风险 | 影响 | 缓解方案 |
|------|------|----------|
| AI 响应延迟 | 对话体验下降 | 添加加载动画 + 流式输出 |
| 语伴匹配率低 | 用户流失 | 扩大匹配范围 + 推荐算法优化 |
| 推送通知被拦截 | 通知到达率低 | 多种通知渠道 + 应用内提醒 |

---

## 六、成功指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **日活用户 (DAU)** | +30% | 后端日志统计 |
| **平均对话轮次** | >5 轮/天 | 对话记录分析 |
| **语伴匹配成功率** | >60% | 匹配算法日志 |
| **PWA 安装率** | >20% | 浏览器统计 |
| **用户留存率 (7 天)** | >50% | 用户行为分析 |

---

## 七、时间线

```
2026-06-19  v4.5.0 发布 ✅
2026-06-22  v5.0.0 规划确认
2026-06-23  Phase 1 启动 (AI 对话)
2026-07-06  Phase 1 完成
2026-07-07  Phase 2 启动 (社交)
2026-07-20  Phase 2 完成
2026-07-21  Phase 3 启动 (可视化)
2026-07-27  Phase 3 完成
2026-07-28  Phase 4 启动 (测试发布)
2026-08-03  v5.0.0 正式发布 🎉
```

---

## 八、附录

### A. API 端点清单

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v2/conversation/start` | POST | 开始新对话 |
| `/api/v2/conversation/message` | POST | 发送消息 |
| `/api/v2/conversation/history` | GET | 获取对话历史 |
| `/api/v2/social/match` | POST | 请求语伴匹配 |
| `/api/v2/social/groups` | GET | 获取群组列表 |
| `/api/v2/social/posts` | GET | 获取动态流 |
| `/api/v2/social/posts` | POST | 发布动态 |
| `/api/v2/analytics/growth` | GET | 获取成长曲线 |
| `/api/v2/analytics/heatmap` | GET | 获取热力图数据 |
| `/api/v2/analytics/report` | GET | 生成学习报告 |

### B. 组件清单

| 组件 | 用途 | 依赖 |
|------|------|------|
| `ChatBubble.vue` | 对话消息气泡 | 无 |
| `MatchCard.vue` | 语伴匹配卡片 | 无 |
| `GroupCard.vue` | 群组卡片 | 无 |
| `PostCard.vue` | 动态卡片 | 无 |
| `GrowthChart.vue` | 成长曲线图 | ECharts |
| `Heatmap.vue` | 学习热力图 | ECharts |
| `WordCloud.vue` | 词云图 | ECharts |

---

**文档版本**: v1.0  
**最后更新**: 2026-06-19  
**负责人**: Ke (GDP 影子)
