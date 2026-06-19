# 🌿 LAWA2 — 产品路线图 v7

> 养成式双语日常空间 × 多 Agent 架构
> 2026-06-17 | 基于 Ke & 达子双人讨论
> 
> **更新日志：**
> - v6 → v7: 更新 Phase 6 实际交付状态，补充 v2.8.0-v3.2.0 版本历史
> - v7 → v8: 新增 Phase 8（全面打磨轮），移除 P7 中实际已完成的子任务，重构版本表

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

### Phase 6：质量增强 + 生产就绪（进行中）

**目标：** 完善内容管理、数据可视化、部署运维

| # | 任务 | 产出 | 优先级 | 状态 |
|---|------|------|--------|------|
| 6.1 | 内容管理页面（前端） | 种子语料 CRUD UI + 双语编辑 | P1 | ✅ v2.8.0 |
| 6.2 | 数据看板图表 | ECharts 集成 + DAU/留存/行为统计 | P1 | ✅ v2.9.0 |
| 6.3 | 日志查看页面 | 系统日志 UI + 错误聚合 | P2 | ✅ v3.0.0 |
| 6.4 | 错误监控 | 异常捕获 + 错误聚合 + API | P2 | ✅ v3.1.0 |
| 6.5 | E2E 测试补全 | Playwright 场景覆盖 + 回归测试 | P2 | ✅ v3.2.0 |
| 6.6 | CI/CD 流水线 | GitHub Actions 自动构建 + 部署 | P3 | ✅ v3.2.0 |
| 6.7 | 统一认证依赖 | 统一 auth 依赖注入 | P1 | ✅ v3.3.0 |
| 6.8 | API 参数标准化 | 所有 Query/Path 参数添加 description | P2 | ✅ v3.4.0 |
| 6.9 | 测试用户管理 | 自动创建/清理测试用户 | P2 | ✅ v3.5.0 |
| 6.10 | 文件上传测试 | multipart/form-data 测试 | P3 | ✅ v3.6.0 |
| 6.11 | 推送路由注册 | 注册 push_router 到主应用 | P2 | ✅ v3.7.0 |
| 6.12 | Push 模块导入 | 添加 Path 导入 | P2 | ✅ v3.7.0 |

**Phase 6 进度：12/12 子任务已完成，P1-P3 级别均已覆盖。**

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

P6  [✅] Phase 6 — 质量增强 + 生产就绪
    目标：内容管理 + 数据可视化 + 部署运维
    状态：12/12 完成
    ✅ 6.1-6.12 全部完成 (v2.8.0-v3.7.0)

P7  [✅] Phase 7 — 质量提升 + 新特性
    目标：Bug 修复 + 词汇卡片 + 桥梁 Lv.4-5
    状态：8/8 子任务完成
    ✅ 7.1 前端功能测试 (v3.8.0)
    ✅ 7.2 性能优化 (v3.8.0)
    ✅ 7.3 文档完善 (v3.8.0)
    ✅ 7.4 并发用户创建 Bug 修复 (v3.9.0)
    ✅ 7.5 修复 milestone 测试 (v4.0.0)
    ✅ 7.6 修复前端构建 (v4.0.0)
    ✅ 7.7 词汇卡片系统（Word Card）(v4.0.0)
    ✅ 7.8 桥梁 Lv.4-5（Group Chat + Offline Scene）(v4.0.0)

P8  [🔲] Phase 8 — 全面打磨轮 (Polishing Sprint)
    目标：现有功能全部打磨到「能用、好用、会用」水平
    时间：2-3 天，不开发新功能
    状态：0/10 子任务完成
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
v2.8.0  2026-06-17  Phase 6: Content Management (Frontend)
v2.9.0  2026-06-17  Phase 6: Data Dashboard Charts
v3.0.0  2026-06-17  Phase 6: Log Viewer Page
v3.1.0  2026-06-17  Phase 6: Error Monitoring
v3.2.0  2026-06-17  Phase 6: E2E Tests + CI/CD Pipeline
v3.3.0  2026-06-18  Phase 6: Unified Auth Dependencies (6.7)
v3.4.0  2026-06-18  Phase 6: API Parameter Standardization (6.8)
v3.5.0  2026-06-18  Phase 6: Test User Management (6.9)
v3.6.0  2026-06-18  Phase 6: File Upload E2E Tests (6.10)
v3.7.0  2026-06-18  Phase 6: Push Router Registration + Import Fix (6.11-6.12)
v3.8.0  2026-06-18  Phase 7: Frontend Tests + Performance + Docs (7.1-7.3)
v3.9.0  2026-06-19  Phase 7: Concurrent User Creation Bug Fix (7.4)
v4.0.0  2026-06-19  Phase 7: Bug Fixes + Word Card System + Bridge Lv.4-5 (7.5-7.8)
v4.1.0  Phase 8: 打磨轮 — 状态修复 + 零配置引导
v4.2.0  Phase 8: 打磨轮 — 空状态 + 错误处理 + 双语补缺
v4.3.0  Phase 8: 打磨轮 — 桥梁 + 卡片 + 拍照精修
v4.4.0  Phase 8: 打磨轮 — 花园 + 画像 + 导航完工
```

---

## 5. 架构变更总结

---

### Phase 7：质量提升 + 新特性

**目标：** 全面功能测试、性能优化、文档完善、新特性开发

| # | 任务 | 产出 | 优先级 | 状态 |
|---|------|------|--------|------|
| 7.1 | 前端功能测试 | 所有页面/交互的端到端测试 | P1 | ✅ v3.8.0 |
| 7.2 | 性能优化 | API < 100ms，Bundle 0.53MB | P1 | ✅ v3.8.0 |
| 7.3 | 文档完善 | API 文档、部署文档、用户手册 | P2 | ✅ v3.8.0 |
| 7.4 | 并发用户创建 Bug 修复 | 重试机制处理 IntegrityError | P0 | ✅ v3.9.0 |
| 7.5 | 修复 milestone 测试 | 调整里程碑检测阈值，满足 single-action 触发 | P0 | 🔲 未开始 |
| 7.6 | 修复前端构建 | 补全 errors.ts/seed.ts/logs.ts/push.ts 缺失导出 | P0 | 🔲 未开始 |
| 7.7 | 词汇卡片系统（Word Card） | 关键词提取 → 卡片保存 → 复习模式 | P1 | 🔲 未开始 |
| 7.8 | 桥梁 Lv.4-5（Group Chat + Offline Scene） | 多语伴讨论 + 离线场景对话 | P1 | 🔲 未开始 |

**Phase 7 进度：8/8 子任务完成 ✅**

**v4.0.0 (2026-06-19) — Bug Fix + Word Card + 前端构建修复**
- 修复 milestone 测试：UUID 动态生成解决数据残留
- 修复前端构建：errors.ts/logs.ts/seed.ts 内联 API 函数
- 修复前端构建：WordCardPage.vue 缺失 `</style>` 闭标签
- 修复 word_card.ts：fetchData/withUser 内联替代 client 导入
- 修复 agent 路由 404/422/500（注册 agent 路由、补 Path 导入、加 `/agent` 代理规则、GET /config 端点、Pydantic Body 参数、方法名匹配）
- 词汇卡片系统：WordCardPage.vue（浏览/复习/统计三 tab）+ 后端 SM-2 算法
- 前端构建 ✅ 1.8s，后端 31/31 测试通过

---

### Phase 8：全面打磨轮 (Polishing Sprint)

**核心理念：** 不开发新功能，集中把现有功能打磨到「能用、好用、会用」水平。

**时长：** 2-3 天，逐项验收，验收通过再前进

**验收标准（每项）：**
1. 🔴 页面加载无报错（Console 无红字）
2. 🟢 交互链路完整（点→等→看，每一步都有反馈）
3. 🟢 空状态优雅（无数据时不死白一片）
4. 🟢 错误提示友好（500 不暴露 stack，422 告诉用户怎么改）
5. 🟢 双语文案补全（所有 UI 文本中英并行）
6. 🟢 加载状态有反馈（skeleton / spinner / 文字提示三选一）
7. 🟢 前后端联调通过（每个页面核心操作走通）

---

### 8.1 状态修复 + 零配置引导

**目标：** 新用户首次打开就能跑起来，不需要懂配置。

| # | 任务 | 现状 | 打磨 |
|---|------|------|------|
| 8.1.1 | 免密码登录简化 | `LoginPage.vue` 点击后直接注册登录，无卡顿提示 | 加 loading 动画 + 登录成功后过渡到首页而不是闪一下 |
| 8.1.2 | 画像页面引导 | `OnboardingPage.vue` 有 4 个步骤 | 加步骤指示器（1/4 2/4 3/4 4/4）+ 完成动画 |
| 8.1.3 | 首次进入首页引导 | 直接展示空仪表盘 | 加 overlay 提示：「试试点这里开始」指向快速操作按钮 |
| 8.1.4 | 首次进入无数据兜底 | 显示空白统计 | 加「还没有数据 · No data yet」+ 示例数据展示 |
| 8.1.5 | Console 错误清零 | `GET /config` 405 已修复，`POST /action` 422 已修复 | 全量扫描一次确保 console 无红字 |

---

### 8.2 空状态 + 错误处理 + 双语补缺

**目标：** 每个页面在无数据/错误状态下都友好，所有文案中英并行。

| # | 任务 | 现状 | 打磨 |
|---|------|------|------|
| 8.2.1 | FeedPage 空状态 | `暂无更多资讯` | 加图标 + 「暂无内容 · Nothing yet」+ 鼓励性文案 + 刷新按钮 |
| 8.2.2 | GardenPage 空状态 | 花园空时可能显示 0 数据 | 加「🌱 你的花园还在萌芽」+ 引导：完成行为后回来查看 |
| 8.2.3 | BridgePage 空状态 | 无历史记录时白板 | 加「🌉 还没有对话 · No conversations yet」+ 开始对话引导 |
| 8.2.4 | PhotoPage 空状态 | 无照片时空白 | 加「📸 拍下你的第一个瞬间」+ 拍照引导 |
| 8.2.5 | ReminderPage 空状态 | 无提醒时空白 | 加「📅 添加你的第一个日程」+ 添加按钮引导 |
| 8.2.6 | WordCardPage 空状态 | 已有空状态但文案不全 | 统一中英并行文案 |
| 8.2.7 | AdminPage 空状态 | 数据看板无数据时可能空白 | 加 N/A 占位 |
| 8.2.8 | 所有页面加载状态 | 部分页面无 loading | 统一补 skeleton 或 spinner |
| 8.2.9 | 所有页面错误捕获 | 网络错误直接抛 console | 统一 catch + toast 提示 + 重试按钮 |
| 8.2.10 | 双语文案扫描 | 逐个页面检查 UI 文本 | 每个 label/placeholder/button 确保中英并行 |

---

### 8.3 桥梁 + 词汇卡片 + 拍照精修

**目标：** 三个特色功能（Bridge / Word Card / Photo）交互体验提升。

| # | 任务 | 现状 | 打磨 |
|---|------|------|------|
| 8.3.1 | Bridge 体验优化 | 对话流步骤清晰 | 增加「打字中」动画效果，提升等待体验 |
| 8.3.2 | Bridge 反馈完善 | 回复后直接显示结果 | 增加对话气泡动画 + 评分高亮 + 重复回复保护 |
| 8.3.3 | Bridge 中英双语检查 | 问候/回复/反馈文案可能不全 | 全量检查，补全 `_en` 后缀文案 |
| 8.3.4 | WordCard 复习体验 | 卡片翻转、复习提交正常工作 | 增加翻转动效 + 连续复习不打断 |
| 8.3.5 | WordCard 统计可视化 | 掌握率进度条已有 | 增加环形图或迷你图表替代纯数字 |
| 8.3.6 | WordCard 添加体验 | modal 表单 | 增加 word 输入自动去空格 + 去重提示 |
| 8.3.7 | Photo 上传体验 | 上传后返回结果 | 增加上传进度条 + 压缩提示 + 失败重试 |
| 8.3.8 | Photo 对话体验 | 气泡式交互 | 增加自动滚动到最新消息 + 中英双语文案检查 |

---

### 8.4 花园 + 画像 + 导航完工

**目标：** 信息花园、用户画像、全局导航的细节完善。

| # | 任务 | 现状 | 打磨 |
|---|------|------|------|
| 8.4.1 | 花园首页仪表盘 | 统计数字展示 | 增加词汇生命周期可视化（种子→幼苗→开花→结果四阶段动画） |
| 8.4.2 | 花园周报 | 文本报告 | 增加简单图表 + 双语报告格式 |
| 8.4.3 | 花园健康度 | 健康分数 | 增加「健康指数」的解读文案（不是只有数字） |
| 8.4.4 | ProfilePage 完善 | 用户信息展示 | 增加统计概览 + 编辑入口 |
| 8.4.5 | 底部导航 | 主 Agent 子导航 tab | 检查所有 tab 名称双语 + 当前 tab 高亮 + 点击后加载态 |
| 8.4.6 | 路由切换平滑 | 页面切换有闪烁 | 加 `<Transition>` 包裹 + 路由切换动画 |
| 8.4.7 | 全站 CSS 一致性 | 各页面有自己的 padding/font | 统一 CSS 变量（--page-padding, --text-size 等） |

---

### Phase 8 分版本规划

```
v4.1.0  — Phase 8.1: 状态修复 + 零配置引导
v4.2.0  — Phase 8.2: 空状态 + 错误处理 + 双语补缺
v4.3.0  — Phase 8.3: 桥梁 + 卡片 + 拍照精修
v4.4.0  — Phase 8.4: 花园 + 画像 + 导航完工
```

**验收清单（总）：**
- [ ] Console 零红字错误
- [ ] 每个页面加载有反馈
- [ ] 每个空状态有友好提示
- [ ] 每个网络错误有 toast + 重试
- [ ] 所有 UI 文本中英并行
- [ ] 登录/画像/首页引导走通
- [ ] 桥架对话流程丝滑
- [ ] 词汇卡片创建+复习+统计走通
- [ ] 拍照上传+对话走通
- [ ] 花园仪表盘有可视化
- [ ] 导航切换动画流畅
- [ ] 前端 build 通过（零 warning）
- [ ] 后端 31/31 测试通过

---

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
