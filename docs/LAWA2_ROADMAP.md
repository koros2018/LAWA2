# 🌿 LAWA2 — 产品路线图 v6

> 养成式双语日常空间 × 多 Agent 架构
> 2026-06-17 | 基于 Ke & 达子双人讨论
> 
> **更新日志：**
> - v5 → v6: 添加 Phase 6（质量增强 + 生产就绪），标记 Phase 5 为已取消

---

## 0. 产品愿景（更新）

**一句话：LAWA2 不教语言，它让用户在两种语言里过生活。**

**核心变化 v4 → v5：**

```
v4：一个学英语的工具 → 用户有"学"的压力
v5：一个中英双语的日常空间 → 用户在用语言，不是在学语言
```

**三层价值（保留）：**

```
Layer 1 — 习惯养成
  Hooked 模型：Trigger → Action → Variable Reward → Investment

Layer 2 — 社交融入
  用户预演真实社交场景，降低现实焦虑

Layer 3 — 双向桥梁
  Alice 与 Bob 互为语伴，获得"我被理解了"的正反馈
```

---

## 1. 产品原则（新增）

### 1.1 全面中英双语（P0，贯穿所有）

从第一眼到使用中的每个角落，都是中英双语的展示：

| 场景 | 现在 | 应该 |
|------|------|------|
| 标题/导航 | 中文 | 中英并行（"花园 · Garden"）|
| 内容卡片 | 目标语言 + 可展开翻译 | 双语言默认可见，字体区分 |
| 空状态 | "暂无数据" | "暂无数据 · Nothing yet" |
| 错误提示 | "网络错误" | "网络错误 · Network error" |
| 按钮 | "开始" | "开始 · Start" |
| 操作反馈 | "已保存" | "已保存 · Saved ✓" |
| 推送通知 | 中文 | 双语 + 文化彩蛋 |

**设计原则：**
- 不区分"目标语言"和"母语"——两种语言同等重要
- 同一信息同时呈现，用户自然吸收
- 语言切换不是"设置"，是"默认状态"

### 1.2 三个 Agent 入口（新架构）

不再是一堆页面/路由，用户只看到三个 Agent：

```
LAWA2
├── 🧠 主 Agent（语言日常）
│   入口：花园 + 桥梁 + 成长洞察
│
├── 📅 事项提醒 Agent
│   入口：日程/纪念日/节假日 → 中英文化融入
│
├── 📸 拍照理解 Agent
│   入口：拍照上传 → AI 理解 → 中英沟通
│
└── ⚙️ 超级管理员 Agent（仅管理员可见）
    入口：用户管理 + 内容管理 + 数据看板
```

### 1.3 数据安全（真实认证）

```
MVP（当前）→ 过渡 → 正式
localStorage  微信扫码  JWT + HTTPS
免密码        OAuth     Session 管理
单一用户     用户数据隔离 多设备同步
```

---

## 2. Agent 架构详细设计

### 2.1 主 Agent（语言日常）— 现有基础

**保留功能（需要双语化）：**
- 语言花园（词簇可视化 + 周报 + 健康度）
- 双向桥梁（Lv.1-5 语伴互动）
- 成长洞察（四维评分 + 趋势 + 曲线）
- 信息流/社交场景（Feed + 理解度）
- 登录/画像（简化认证 + 两步画像）

**改造重点：**
- 所有 UI 文案中英双语化
- 底部导航改为 Agent 选择器（主 Agent / 提醒 Agent / 拍照 Agent）
- 统一入口风格，不再是分散页面

### 2.2 事项提醒 Agent（新建）

**核心逻辑：** 将用户的日程、计划、待办、节假日、纪念日等融入产品，让用户真实体会中英文化。

| 能力 | 说明 | 优先级 |
|------|------|--------|
| 日程同步 | 用户手动添加 / 未来可接入日历 API | P1 |
| 纪念日管理 | 生日、周年纪念 → 自动生成中英祝福语 | P1 |
| 节假日推送 | 中国节日 + 西方节日，双语文化背景解释 | P1 |
| 待办事项 | 简单 TODO 列表，完成时中英双语文案 | P2 |
| 定时提醒 | 每日/每周提醒，内容来自用户设定或系统推荐 | P2 |
| 文化彩蛋 | 节日前推送："明天是端午节！来看粽子用英语怎么说" | P2 |

**UI 形态：**
- 日历视图（月历 + 事件标记）
- 列表视图（按日期排列）
- 推送通知（双语）

**数据模型：**

```
ReminderEvent
  id / user_id / title / title_en / date / event_type / note / is_done / created_at

EventType: personal / holiday / todo / anniversary
```

### 2.3 拍照理解 Agent（新建）

**核心逻辑：** 用户随手拍照上传，AI 理解图片内容，用双语描述并展开对话。

| 能力 | 说明 | 优先级 |
|------|------|--------|
| 图片上传 | 拍照或相册选择 | P1 |
| AI 理解 | 描述图片内容（中英双语） | P1 |
| 对话互动 | 基于图片内容的中英问答 | P1 |
| 词汇提取 | 从描述中提取关键词 + 双语释义 | P2 |
| 场景标签 | 自动识别场景类型（美食/风景/日常等） | P2 |
| 分享到桥梁 | 把图片分享给语伴讨论 | P3 |

**UI 形态：**
- 拍照按钮（大圆按钮，类似微信拍照）
- 图片预览 + AI 描述
- 对话气泡（用户回复 → AI 继续）

**数据模型：**

```
PhotoUnderstanding
  id / user_id / image_path / ai_description / ai_description_en
  extracted_words / scene_tags / created_at

PhotoChat
  id / photo_id / role / content / content_en / created_at
```

### 2.4 超级管理员 Agent（新建）

**核心逻辑：** 后台管理，数据看板，内容运营。

| 能力 | 说明 | 优先级 |
|------|------|--------|
| 用户管理 | 用户列表 / 状态 / 数据 | P1 |
| 内容管理 | 种子语料 / 社交场景 / 推送内容 CRUD | P1 |
| 数据看板 | 日活 / 留存 / 行为统计 / 桥梁活跃度 | P2 |
| 日志查看 | 系统日志 / 错误追踪 | P2 |
| 配置管理 | Hooked 参数 / 奖励配置 / 推送频率 | P3 |

---

## 3. 分阶段交付计划

### Phase 0：现有基础（已交付）

```
✅ 项目初始化（FastAPI + Vue3/Vite/TypeScript + SQLite）
✅ 核心四引擎（Action / Reward / Trigger / Investment）
✅ 前端 UI（极简哲思 × 灵幻风格 × 移动优先）
✅ 登录/画像（简化认证 + 两步画像）
✅ 语言花园（词簇 + 周报 + 健康度 + 成长曲线）
✅ 双向桥梁 Lv.1-3（问候 + 点赞 + 教梗）
✅ 代码重构（老 RPG 移入 legacy/）
✅ 20+ API 端点（全部通过验证）
✅ 前端构建通过
```

### Phase 1：双语化 + Agent 架构重构（预计：2天）

**目标：** 所有 UI 中英双语 + 页面结构改为三 Agent 入口

| # | 任务 | 产出 | 备注 |
|---|------|------|------|
| 1.1 | 设计系统双语化 | 所有 CSS 变量 + 组件支持双语文案 | 贯穿性改动 |
| 1.2 | 底部导航改为 Agent 选择器 | 三个 Agent Tab（主/提醒/拍照）+ 管理入口 | 路由重构 |
| 1.3 | 花园页面双语化 | 所有文案中英并行 | 主 Agent 核心 |
| 1.4 | 桥梁页面双语化 | 语伴名/问候/回复/结果双语 | 主 Agent 核心 |
| 1.5 | Feed/画像/登录双语化 | 统一双语风格 | 主 Agent 辅助 |
| 1.6 | API 响应双语字段 | 后端返回 content_en 等字段 | 前端渲染准备 |

**API 变更：**
```
  所有 GET 响应增加 _en 字段（英文文案）
  新增 GET /api/v2/agent/status — 三个 Agent 状态概览
```

### Phase 2：事项提醒 Agent（预计：2天）

**目标：** 可用的提醒 + 日历 + 纪念日功能

| # | 任务 | 产出 |
|---|------|------|
| 2.1 | 数据模型 + 数据库迁移 | ReminderEvent 表 + 索引 |
| 2.2 | 后端 CRUD API | 增删改查 + 按日期范围查询 |
| 2.3 | 节假日种子数据 | 中国节日 + 西方节日 + 中英文化背景 |
| 2.4 | 前端日历组件 | 月历 + 事件标记 + 点击查看详情 |
| 2.5 | 前端添加/编辑表单 | 标题/日期/类型/备注双语输入 |
| 2.6 | 推送通知集成 | 定时检查 + 双语推送（基于现有 Trigger Engine）|
| 2.7 | 纪念日自动祝福 | 生日/周年 → 自动生成中英文祝福卡片 |

**API 变更：**
```
  GET    /api/v2/reminder/events?date=YYYY-MM-DD
  POST   /api/v2/reminder/events
  PUT    /api/v2/reminder/events/:id
  DELETE /api/v2/reminder/events/:id
  GET    /api/v2/reminder/upcoming — 即将到来事件
  GET    /api/v2/reminder/holidays — 节假日列表（含文化背景）
  POST   /api/v2/reminder/generate-greeting — 生成纪念日中英祝福
```

### Phase 3：拍照理解 Agent（预计：2天）

**目标：** 拍照上传 → AI 理解 → 中英对话

| # | 任务 | 产出 |
|---|------|------|
| 3.1 | 图片上传后端 | 文件存储 + 缩略图 + 类型校验 |
| 3.2 | AI 图片理解集成 | 接入图像理解模型（LLaVA / GPT-4V 等）|
| 3.3 | 图片描述 API | 中英双语描述生成 + 关键词提取 |
| 3.4 | 基于图片的对话 | 上下文对话 + 语言水平适配 |
| 3.5 | 前端拍照/上传组件 | 拍照按钮 + 预览 + 加载动画 |
| 3.6 | 前端对话组件 | 气泡式交互 + 中英双语 |
| 3.7 | 词汇卡片弹出 | 关键词 → 中英释义 + 例句 |

**API 变更：**
```
  POST   /api/v2/photo/upload — 上传图片
  POST   /api/v2/photo/:id/chat — 基于图片对话
  GET    /api/v2/photo/:id — 获取图片详情 + 描述
  GET    /api/v2/photo/:id/words — 提取的关键词
  GET    /api/v2/photo/history — 历史图片列表
```

### Phase 4：超级管理员 Agent（预计：1天）

**目标：** 后台管理 + 数据看板

| # | 任务 | 产出 |
|---|------|------|
| 4.1 | 管理员认证 | 独立登录 + 角色验证 |
| 4.2 | 用户管理页面 | 列表/搜索/详情/禁用 |
| 4.3 | 内容管理页面 | 语料/场景/推送内容 CRUD |
| 4.4 | 数据看板 | DAU/留存/行为统计图表 |
| 4.5 | 日志查看 | 后端日志 + 错误聚合 |

**API 变更：**
```
  POST   /api/v2/admin/login
  GET    /api/v2/admin/users — 用户列表
  GET    /api/v2/admin/users/:id — 用户详情
  POST   /api/v2/admin/seed-content — 内容管理 CRUD
  GET    /api/v2/admin/stats — 数据统计
  GET    /api/v2/admin/logs — 日志查看
```

### Phase 5：微信登录 + 数据安全（预计：1天）

**目标：** 从 localStorage MVP 升级到真实认证

| # | 任务 | 产出 |
|---|------|------|
| 5.1 | 微信扫码登录 | OAuth 流程 + 回调处理 |
| 5.2 | JWT Session 管理 | Token 签发/刷新/吊销 |
| 5.3 | 用户数据隔离 | 多用户数据安全 + 权限校验 |
| 5.4 | HTTPS 配置 | 开发环境 mkcert + 生产环境证书 |
| 5.5 | 迁移已有用户 | localStorage → 后端认证平滑迁移 |

> ⚠️ **已取消** — 2026-06-17 决定移除所有 OAuth（GitHub + WeChat），仅保留免密码登录

---

### Phase 6：质量增强 + 生产就绪（新增）

**目标：** 完善内容管理、数据可视化、部署运维

| # | 任务 | 产出 | 优先级 |
|---|------|------|--------|
| 6.1 | 内容管理页面（前端） | 种子语料 CRUD UI + 双语编辑 | P1 |
| 6.2 | 数据看板图表 | ECharts 集成 + DAU/留存/行为统计 | P1 |
| 6.3 | 日志查看页面 | 系统日志 UI + 错误聚合 | P2 |
| 6.4 | 错误监控 | Sentry 集成 + 异常告警 | P2 |
| 6.5 | E2E 测试补全 | Playwright 场景覆盖 + 回归测试 | P2 |
| 6.6 | CI/CD 流水线 | GitHub Actions 自动构建 + 部署 | P3 |
| 6.7 | 数据备份/恢复 | 自动备份脚本 + 恢复流程 | ✅ 已完成 |
| 6.8 | Docker 部署 | Dockerfile + docker-compose.yml | ✅ 已完成 |

**API 变更：**
```
  GET    /api/v2/seed/contents — 种子语料列表
  POST   /api/v2/seed/contents — 创建种子语料
  PUT    /api/v2/seed/contents/:id — 更新种子语料
  DELETE /api/v2/seed/contents/:id — 删除种子语料
  GET    /api/v2/seed/contents/system/:type — 系统内置语料
```

---

## 4. 里程碑

```
M0  [✅] 2026-06-13 — 核心循环可运行
M1  [✅] 2026-06-14 — 前端可体验
M2  [✅] 2026-06-14 — 社交场景上线
M3  [✅] 2026-06-14 — 双向桥梁 Lv.1
M4  [✅] 2026-06-15 — 花园+洞察深化 + 桥梁 Lv.2-3

P1  [✅] Phase 1 — 全面双语化 + Agent 架构
    目标：所有 UI 中英双语 + 三 Agent 入口
P2  [✅] Phase 2 — 事项提醒 Agent
    目标：日历/纪念日/节假日中英文化融入
P3  [✅] Phase 3 — 拍照理解 Agent
    目标：拍照上传 → AI 理解 → 中英对话
P4  [✅] Phase 4 — 超级管理员 Agent
    目标：后台管理 + 数据看板
P5  [❌] Phase 5 — 微信登录 + 数据安全
    目标：真实认证 + 用户数据隔离
    状态：已取消（2026-06-17），仅保留免密码登录

P6  [🔲] Phase 6 — 质量增强 + 生产就绪
    目标：内容管理 + 数据可视化 + 部署运维
    状态：进行中（2026-06-17）
```

---

## 5. 版本历史

```
v2.0.0  2026-06-12  Core Loop + Bridge Lv.1-3
v2.1.0  2026-06-13  Photo Understanding Agent
v2.2.0  2026-06-16  Admin Agent + GitHub OAuth + JWT
v2.3.0  2026-06-17  Bridge Lv.4-5 (Group Chat + Offline Scene)
v2.3.1  2026-06-17  Photo Thumbnail
v2.4.0  2026-06-17  Phase 1 Full Bilingualization
v2.5.0  2026-06-17  Push Notifications + Word Card Modal + Share to Bridge
v2.6.0  2026-06-17  3-Agent Entry Architecture + Admin Enhancement
v2.7.0  2026-06-17  3-Agent Frontend Integration
v2.7.1  2026-06-17  Admin Permission Check (is_admin field)
v2.7.2  2026-06-17  Register Admin User + Remove GitHub OAuth
v2.7.3  2026-06-17  Admin Permission Enforcement + OAuth UI Cleanup
v2.7.4  2026-06-17  Remove all OAuth (GitHub + WeChat)
v2.7.5  2026-06-17  Deployment Scripts + Data Backup/Restore
v2.8.0  TBD       Phase 6: Content Management (Frontend)
v2.9.0  TBD       Phase 6: Data Dashboard Charts
v3.0.0  TBD       Phase 6: Production Ready
```

---

## 5. 架构变更总结

### 路由架构（更新后）

```
前：10+ 分散路由
后：4 个 Agent + 统一入口

/ → 主 Agent（首页路由）
/agent/reminder → 事项提醒 Agent
/agent/photo → 拍照理解 Agent
/admin → 超级管理员 Agent
```

### 后端目录结构

```
src/
├── agent/
│   ├── main_agent/         # 主 Agent（现有 habit/bridge/auth）
│   ├── reminder_agent/     # 事项提醒 Agent（新建）
│   ├── photo_agent/        # 拍照理解 Agent（新建）
│   └── admin_agent/        # 超级管理员 Agent（新建）
├── engine/                 # 共享引擎（现有）
├── models/                 # 数据模型（扩展）
├── routes/                 # 路由注册（简化）
└── middleware/             # 认证/权限中间件（新增）
```

### 前端目录结构

```
frontend/src/
├── views/
│   ├── MainAgent.vue       # 主 Agent（原有页面整合）
│   ├── ReminderAgent.vue   # 事项提醒 Agent（新建）
│   ├── PhotoAgent.vue      # 拍照理解 Agent（新建）
│   └── AdminAgent.vue      # 超级管理员 Agent（新建）
├── components/
│   ├── bilingual/          # 双语组件（新建）
│   └── ... (现有)
├── api/
│   ├── habit.ts            # 主 Agent API
│   ├── bridge.ts           # 桥梁 API
│   ├── reminder.ts         # 提醒 API（新建）
│   ├── photo.ts            # 拍照 API（新建）
│   └── admin.ts            # 管理 API（新建）
└── router/
    └── index.ts            # 路由（更新）
```

---

## 6. 相关文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 习惯引擎设计 | `docs/LAWA_HABIT_ENGINE.md` | 核心 Hooked 四步引擎 |
| 社交融入设计 | `docs/LAWA_SOCIAL_IMMERSION.md` | 社交场景语料 + 预演 |
| 本路线图 | `docs/LAWA2_ROADMAP.md` | 全景规划 + Phase 拆分 |

---

*养成式双语日常空间 × 多 Agent 架构*
*设计者：Ke & 达子 | 2026-06-15*
