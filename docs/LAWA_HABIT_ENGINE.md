# 🌿 LAWA 养成引擎 — 详细设计文档

> 基于《Hooked》模型的习惯养成式语言学习系统
> 设计日期：2026-06-13
> 设计者：Ke（架构师）& 达子（实施）
> 学术依据版本：v2（2026-06-13 18:36 更新）
> 参见附录A：理论参考文献

---

## 0. 学术理论框架（设计根基）

### 0.1 核心理念来源

本设计基于**三重理论交叉验证**：

| 理论体系 | 核心模型 | 贡献维度 |
|----------|----------|----------|
| **习惯形成理论** | Hooked (Eyal, 2014) + Fogg Behavior Model (2009) | 用户行为引擎（Trigger-Action-Reward-Investment）|
| **第二语言习得** | Krashen (1985) + Nation (2001) + Schmidt (1990) | 语言习得机制（可理解输入/词汇复现/注意假说）|
| **自适应AI系统** | Aleven et al. (2017) + Settles et al. (2018) | AI介入策略（何时/如何介入，沉默与开口）|

### 0.2 为什么

---

## 一、核心理念

### 🚫 被拒绝的旧范式：RPG 化
- "打副本获取经验" → 人为割裂学习与生活
- "职业/等级/装备" → 游戏化表层，无法持久
- "每日打卡" → 强迫行为，非习惯养成
- 理论依据：Hamari et al. (2014) 元分析显示游戏化效果短期显著但长期衰减

### ✅ 新范式：养成式习惯引擎
- **语言能力不是"练"出来的，是"养"出来的**
- 用户不觉得自己在"学习"，但语言能力确实在提升
- 日常信息流即学习材料，生活场景即练习场
- 理论依据：Fogg (2009) 行为模型 + Eyal (2014) Hooked 模型的交叉验证

### 📖 《Hooked》四步模型映射

| Hooked 步骤 | LAWA 实现 | 用户感知 |
|-------------|-----------|----------|
| **Trigger** | 日常信息流嵌入（晨间资讯、午间推文、晚间回顾） | "有用/有趣的信息来了" |
| **Action** | 最小行为单元（3次点击、30秒、零挫败感） | "顺便看一下" |
| **Variable Reward** | 不可预测的成长惊喜（新词发现、理解突破、文化彩蛋） | "居然看懂了！" |
| **Investment** | 个人语言资产（词汇本、日记、互动历史、理解曲线） | "这是我的语言花园" |

---

## 二、系统架构

### 2.1 模块关系

```
用户日常生活
    │
    ▼
┌─────────────────────────────────────────────┐
│            LAWA 养成引擎（核心）              │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Trigger  │  │  Action  │  │  Reward  │  │
│  │  Engine  │→│  Engine  │→│  Engine  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       │              │              │        │
│       ▼              ▼              ▼        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 信息流   │  │ 微行为   │  │ 可变    │  │
│  │ 适配器   │  │ 引擎     │  │ 奖励系统 │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│       │              │              │        │
│       ▼              ▼              ▼        │
│  ┌─────────────────────────────────────┐    │
│  │         Investment Engine           │    │
│  │  (语言资产 → 退出成本 → 粘性)       │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│           底层能力（复用现有）               │
│  - 评估引擎（Assessment Engine）            │
│  - 词汇服务（Vocabulary Service）           │
│  - 同伴对话（Companion Agent）             │
│  - 学习计划（Plan Agent）                   │
│  - 用户画像（LawaProfile）                  │
│  - 数据库（SQLite / PostgreSQL 双轨）      │
└─────────────────────────────────────────────┘
```

### 2.2 新增模块（将现有 RPG 代码改造）

**移除或重命名：**
- `src/models/equipment.py` → 改造为 `trophies.py`（成就奖杯，非装备）
- `src/models/quest.py` → 改造为 `micro_habits.py`（微习惯，非任务）
- `src/models/guild.py` → 改造为 `circles.py`（兴趣圈，非公会）
- `src/models/achievement.py` → 保留但重命名，贴合"成长里程碑"
- `src/models/world.py` → 改造为 `flows.py`（信息流场景，非世界地图）
- `src/models/coin.py` → 保留，但改名为"成长积分"
- `src/routes/rpg/` → 改造为 `src/routes/habit/`
- `src/agent/` 相关 agent 重构

**新增模块：**
- `src/engine/` — 养成引擎核心逻辑
  - `trigger_engine.py` — 触发引擎（信息流推送）
  - `action_engine.py` — 行为引擎（微习惯执行）
  - `reward_engine.py` — 奖励引擎（可变奖励分发）
  - `investment_engine.py` — 投入引擎（语言资产沉淀）
- `src/models/habit.py` — 习惯数据模型
- `src/services/info_feeder.py` — 信息流适配器
- `src/services/insight_generator.py` — 成长洞察生成

### 2.3 数据库模型变更

#### 新增表
```sql
-- 用户习惯配置
user_habit_config (
    user_id UUID PK → lawa_profiles.id,
    trigger_time_slot TEXT,      -- 'morning'|'noon'|'evening'
    info_source_prefs JSON,      -- ['news','social','tech','entertainment']
    action_prefs JSON,           -- ['read','listen','speak','write']
    reward_frequency TEXT,       -- 'casual'|'balanced'|'intense'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- 每日信息流记录
daily_info_feed (
    id UUID PK,
    user_id UUID FK,
    feed_date DATE,
    source TEXT,                 -- 'news'|'tweet'|'video'|'article'
    source_url TEXT,
    original_text TEXT,
    difficulty_level TEXT,       -- 'easy'|'medium'|'hard'|'native'
    user_interaction TEXT,       -- 'read'|'listened'|'responded'|'skipped'
    vocab_extracted JSON,        -- 自动提取的词汇
    comprehension_score FLOAT,   -- 理解度评分 (0-1)
    created_at TIMESTAMP
)

-- 微习惯日志
micro_habit_log (
    id UUID PK,
    user_id UUID FK,
    habit_code TEXT,             -- 'read_one_post'|'listen_one_min'|'say_one_thing'|'write_one_sentence'
    triggered_by TEXT,           -- 'trigger_engine'|'manual'
    duration_seconds INT,        -- 实际耗时
    completion_status TEXT,      -- 'completed'|'partial'|'skipped'
    xp_earned INT,
    created_at TIMESTAMP
)

-- 可变奖励记录
variable_reward (
    id UUID PK,
    user_id UUID FK,
    reward_type TEXT,            -- 'vocab_discovery'|'comprehension_breakthrough'|'culture_egg'
    reward_value JSON,           -- 奖励详情
    surprise_level INT,          -- 惊喜程度 1-5
    xp_bonus INT,
    created_at TIMESTAMP
)

-- 语言资产（Investment 核心）
language_asset (
    id UUID PK,
    user_id UUID FK,
    asset_type TEXT,             -- 'vocab_collection'|'sentence_book'|'diary_entry'|'interaction_log'
    asset_data JSON,             -- 具体内容
    word_count INT,
    created_at TIMESTAMP,
    last_accessed TIMESTAMP
)

-- 成长里程碑（替代 achievements）
growth_milestone (
    id UUID PK,
    user_id UUID FK,
    milestone_code TEXT,         -- 'first_100_words'|'first_native_post'|'100_day_streak'
    milestone_name TEXT,
    milestone_description TEXT,
    unlocked_at TIMESTAMP,
    celebration_type TEXT        -- 'confetti'|'story'|'badge'
)
```

#### 改造现有表
```sql
-- lawa_profiles 增加字段
ALTER TABLE lawa_profiles ADD COLUMN habit_level INT DEFAULT 1;        -- 习惯等级
ALTER TABLE lawa_profiles ADD COLUMN growth_xp INT DEFAULT 0;          -- 成长经验值
ALTER TABLE lawa_profiles ADD COLUMN last_feed_date DATE;              -- 最后投喂日期
ALTER TABLE lawa_profiles ADD COLUMN streak_days INT DEFAULT 0;        -- 连续天数
ALTER TABLE lawa_profiles ADD COLUMN language_garden_data JSON;        -- "语言花园"状态
```

### 2.4 API 端点设计

```
旧端点（改造）：
  /api/v1/rpg/* → /api/v1/habit/*

新端点：
  POST   /api/v1/habit/feed              — 获取今日信息流
  POST   /api/v1/habit/action            — 记录一个微行为
  GET    /api/v1/habit/reward            — 领取可变奖励（每日可领 1-3 次）
  GET    /api/v1/habit/garden            — 查看语言花园状态
  POST   /api/v1/habit/garden/water      — "浇水"（投入式互动）
  GET    /api/v1/habit/insight           — 成长洞察
  GET    /api/v1/habit/milestones        — 里程碑列表
  GET    /api/v1/habit/streak            — 连续天数/习惯健康度
  PUT    /api/v1/habit/config            — 更新习惯偏好
  GET    /api/v1/habit/config            — 获取习惯偏好

Agent 端点保留（改造）：
  POST   /api/v1/companion/start         — 保留（和养成引擎联动）
  POST   /api/v1/plan/generate           — 保留（习惯式学习计划）
```

---

## 三、核心流程详解

### 3.1 Trigger Engine（触发引擎）

**功能**：在用户日常信息流中嵌入英文内容，触发学习行为

```
流程：
1. 用户打开 LAWA（或收到推送通知）
2. Trigger Engine 获取用户偏好（兴趣领域、当前水平、历史互动）
3. 从外部源/本地库提取一条符合用户水平的英文内容
4. 包装为"资讯卡片"推送给用户
5. 记录推送结果（用户是否查看、耗时、理解度）

推送时机（用户可配置）：
  - 🌅 晨间（07:00-09:00）：一日之始，推送今日资讯
  - 🌤 午间（12:00-14:00）：刷手机时间，推送趣味内容
  - 🌙 晚间（21:00-23:00）：回顾时刻，推送今日遇到的表达

内容类型：
  - news_brief：简短新闻（50-100词）
  - social_post：社交媒体帖子（30-80词）
  - fun_fact：趣味冷知识（20-50词）
  - vocab_card：今天新遇到的词汇
  - cultural_tip：文化小贴士
```

**关键设计原则**：
- 每次推送不超过 3 分钟阅读量
- 推送内容 90% 可理解（用户能看懂大部分）
- 10% 是"略难但可猜"的新内容（这就是成长点）
- 不推送"教育内容"（如语法讲解），只推送"真实内容"

### 3.2 Action Engine（行为引擎）

**功能**：将语言互动拆解为"不可能失败"的微行为

```
行为类型：
  ⚡ read_one_post    — 读完一条资讯（10-60秒）
  ⚡ listen_one_min   — 听一段30秒音频
  ⚡ say_one_thing    — 跟读/复述一句话
  ⚡ write_one_sentence — 写一句话（日记/评论/想法）
  ⚡ look_up_one      — 查一个不认识的词

行为链（自动串联）：
  读完资讯 → "有个词不认识？点一下查" → "要跟读吗？" → "记下来"
  每次行动都极小，每次完成都有正反馈

零挫败保障：
  - 任何时候可以跳过（无惩罚）
  - 没时间 → "收藏了，下次看"
  - 不想读 → "换一条"
  - 读不懂 → "显示中文对照"
```

**关键设计原则**：
- 最小行为单元 < 30 秒
- 每次行为完成后，用户感觉"赚到了"而非"终于做完了"
- 行为链的设计遵循"流"理论——从一个行为自然流入下一个

### 3.3 Reward Engine（奖励引擎）

**功能**：提供不可预测的可变奖励，保持用户好奇心

```
奖励类型（可变性从低到高）：

🎁 低可变性（日常基础）：
  - 完成微行为 → 成长积分 +1
  - 连续行为 → 积分递增（1, 2, 3, 5...）
  - 理解度提升 → 可视化进度条前进

🎁 中可变性（每日惊喜）：
  - 今日新词发现 → "你遇到了一个稀有词汇！"
  - 理解突破 → "这篇上周你还看不懂的文章，今天能看懂80%了"
  - 文化彩蛋 → 内容背后隐藏的文化故事

🎁 高可变性（随机事件）：
  - 语言花园开花 → 一个随机词汇自动开花（完全掌握）
  - 稀有表达掉落 → 一句地道的俚语/习语
  - 成长洞察 → "你最近最常遇到的词类是..."
  - 跨语言发现 → "这个词在XX语言里也有！"

奖励分发策略：
  - 每天第一次打开 → 必得一个中可变奖励
  - 每完成3个微行为 → 可得一个随机奖励
  - 每周 → 一个高可变奖励
  - 连续7天 → 必得稀有奖励
```

**关键设计原则**：
- 可预测的奖励 = 无聊。用户知道会得到什么就没意思了
- 但完全不预测 = 焦虑。用户需要知道"只要打开就有好事"
- 折中：**打开就有"基础的"，但不知道"额外的"是什么**
- 模仿社交媒体刷新 → 下拉总有好东西

### 3.4 Investment Engine（投入引擎）

**功能**：用户投入越多，退出成本越高，形成习惯粘性

```
投入类型：
  📚 词汇收藏 → 用户"收集"的词汇库
  📝 句子摘录 → 用户收藏/标记的精彩句子
  📖 日记历史 → 用户写过的每一句话
  💬 对话记录 → 和AI/语伴的每一次交流
  📊 理解曲线 → 随时间变化的理解度趋势
  🏆 里程碑 → 所有"第一次"的纪念

"语言花园"可视化：
  每一棵"植物"代表一个词汇/表达
  - 种子 → 第一次遇到
  - 发芽 → 查过/用过一次
  - 幼苗 → 主动使用过
  - 开花 → 完全掌握
  - 结果 → 能在真实场景中自如运用

退出成本设计：
  - 用户的花园越长越茂盛，越舍不得放弃
  - "你的花园已经有 236 棵植物了，确定要让它枯萎吗？"
  - 即使离开一周，花园也只会"休眠"不会"死亡"
  - 回来时 → "欢迎回来！你的花园长出了新芽 🌱"
```

**关键设计原则**：
- 投入必须是**用户主动的选择**（不是系统强制）
- 投入越高 → 看到的"花园"越美 → 越舍不得离开
- 但离开不惩罚 → "休眠"而非"死亡" → 随时可以回来

---

## 四、用户旅程示例

### Day 1（新用户）
```
07:30  推送通知："早安！你的语言花园今天有一粒新种子 🌱"
        ↓ 打开 App
        ↓ 看到一条英文资讯："AI learns to write poetry"
        ↓ 花了 45 秒读完（懂了 70%）
        ↓ 系统："有个词 'metaphor' 不认识？点一下"
        ↓ 查了，记下了 → 词汇收藏 +1
        ↓ 系统："要跟读最后一句吗？"
        ↓ 录了 3 秒 → 评分 85
        ↓ 关闭 App → 总耗时 2 分钟

12:30  推送通知："午间趣闻 🐱"
        ↓ 打开，看了一篇关于猫的英文趣事
        ↓ 发现 "purr" 这个词 → 查了
        ↓ 系统弹出："🎉 你发现了今天的稀有词汇！"
        ↓ 关闭 → 耗时 1 分钟

21:00  推送通知："🌙 晚间回顾"
        ↓ 打开 → 看到今日总结：
           - 读了 2 篇英文内容
           - 学习了 3 个新词（metaphor, purr, whiskers）
           - 跟读了 1 次
           - 理解度进步了 5%
        ↓ 系统："你的语言花园今天长出了 3 片新叶子"
        ↓ 关闭 → 耗时 30 秒

Day 1 总计：约 4 分钟，3 次打开
用户感知："我没学英语，我只是看了一些有趣的东西"
```

### Day 7（习惯形成期）
```
07:30  推送 → 打开 → 发现今天的内容里出现了 "metaphor"
       系统弹出："🎊 你上周学的词出现了！还记得吗？"
       用户 → 真的记得！
       系统："这个词已从'种子'升级为'幼苗'"
       → 成就感 + 惊喜

12:30  推送 → 打开 → 看到一条中文对照的英文资讯
       用户发现："咦，这次好像不用看中文也能看懂大部分"
       系统       系统显示理解度曲线："过去7天你的理解度从65%提升到了78%"
       → "原来我真的在进步！"
       → 这是 Investment 的体现——用户看到了自己的成长轨迹

21:00  推送 → 打开 → 看到"你的语言花园周报"
       - 本周新词：23 个
       - 种子→幼苗：5 个
       - 首次开花：1 个（"metaphor"）
       - 连续天数：7 🔥
       - 击败了 83% 同水平用户
       → 系统弹出可变奖励："🎁 你获得了一个稀有徽章：'一周园丁'"
       
Day 7 小结：用户已经形成了"早中晚看 LAWA"的习惯
用户感知："我不在学英语，我在养我的花园。它越长越好了。"
```

---

## 五、与现有系统的关系

### 5.1 保留的现有功能
- **评估引擎**（Assessment Engine）— 用于初始水平检测和定期成长测量
- **同伴对话**（Companion Agent）— 保留，作为"主动练习"的入口
- **学习计划**（Plan Agent）— 保留，作为"想系统学"用户的选项
- **词汇服务**（Vocabulary Service）— 核心依赖，用于内容难度适配
- **用户画像**（LawaProfile）— 扩展字段

### 5.2 改造的现有功能
- **RPG 世界地图** → 语言花园可视化（更抽象/情感化，而非地图）
- **任务/副本** → 微习惯链（更轻量，嵌入日常）
- **装备/道具** → 成就奖杯（去掉"游戏化"的外壳）
- **公会** → 兴趣圈（去掉竞争元素，保留社交）
- **金币经济** → 成长积分（去货币化，变成纯粹的进步指标）

### 5.3 弃用的 RPG 概念
- ❌ 职业系统（创业者/金融从业者等）— 标签化，不贴合"养成"
- ❌ 技能树 — 过于结构化，限制自然习得
- ❌ 团队副本 — 协调成本高，不适合轻量习惯
- ❌ 装备强化/合成 — 游戏化表层

---

## 六、实施 Sprint 拆分

### Sprint 1：核心循环（第1天）
- [ ] 创建 `src/engine/` 目录及 4 个引擎骨架
- [ ] 实现 Action Engine（最小行为单元）
- [ ] 实现 Reward Engine（基础可变奖励）
- [ ] 新增数据模型：`micro_habit_log`, `variable_reward`
- [ ] 基础 API：`POST /api/v1/habit/action`, `GET /api/v1/habit/reward`
- [ ] 测试：3 个核心流程测试

### Sprint 2：触发引擎 + 信息流（第2天）
- [ ] 实现 Trigger Engine（信息流适配）
- [ ] 实现信息流内容源（本地种子内容库）
- [ ] 新增数据模型：`daily_info_feed`
- [ ] API：`POST /api/v1/habit/feed`, `GET /api/v1/habit/config`
- [ ] 晨/午/晚三段推送逻辑
- [ ] 测试：推送流程 + 内容适配

### Sprint 3：语言花园 + 投入引擎（第3天）
- [ ] 实现 Investment Engine（语言资产沉淀）
- [ ] 新增数据模型：`language_asset`, `growth_milestone`
- [ ] "语言花园"可视化逻辑（词汇生命周期）
- [ ] API：`GET /api/v1/habit/garden`, `POST /api/v1/habit/garden/water`
- [ ] 里程碑检测与庆祝
- [ ] 测试：资产沉淀 + 里程碑触发

### Sprint 4：成长洞察 + 数据深化（第4天）
- [ ] 实现成长洞察生成（Insight Generator）
- [ ] 理解度曲线计算
- [ ] 连续天数 / 习惯健康度
- [ ] API：`GET /api/v1/habit/insight`, `GET /api/v1/habit/streak`
- [ ] 用户偏好配置持久化
- [ ] 测试：洞察生成 + 曲线计算

### Sprint 5：现有 RPG 代码迁移（第5天）
- [ ] 重命名/重构现有模型
- [ ] `routes/rpg/` → `routes/habit/`
- [ ] 更新 Agent 引用
- [ ] 数据迁移脚本（如果已有生产数据）
- [ ] 全面回归测试

### Sprint 6：前端整合（第6天）
- [ ] 信息流卡片 UI
- [ ] 语言花园可视化（前端组件）
- [ ] 微行为交互流
- [ ] 成长洞察面板
- [ ] E2E 测试

---

## 七、关键指标

| 指标 | 目标值 | 衡量方式 |
|------|--------|----------|
| 日均打开次数 | ≥ 2 次 | 日志统计 |
| 日均主动行为 | ≥ 3 个微行为 | micro_habit_log 统计 |
| 7日留存 | ≥ 70% | 连续7天有行为的用户比例 |
| 30日留存 | ≥ 50% | 连续30天有行为的用户比例 |
| 单次耗时 | ≤ 3 分钟 | 平均会话时长 |
| 理解度提升 | 30 天 +20% | 评估引擎定期测量 |
| 词汇自然习得 | 30 天 100+ 词 | 词汇收藏统计 |
| 用户满意度 | NPS ≥ 40 | 定期调研 |

---

## 八、附录：与《Hooked》模型的严格映射

| Hooked 阶段 | LAWA 实现细节 | 《Hooked》原文引用 |
|-------------|---------------|-------------------|
| **External Trigger** | 早中晚三段推送（可配置） | "Calls-to-action that tell the user what to do next" |
| **Internal Trigger** | "我想看懂这条推文" / "这个词好像见过" | "When a behavior becomes a habit, the trigger is internal" |
| **Action** | 3 次点击 / 30 秒 / 零挫败 | "The simplest behavior in anticipation of a reward" |
| **Variable Reward** | 稀有词汇 / 理解突破 / 文化彩蛋 / 花园开花 | "The tribe, the hunt, and the self" (Social/Hunt/Self) |
| **Investment** | 词汇收藏 / 日记历史 / 对话记录 / 理解曲线 | "The more users invest, the more valuable the service becomes" |
| **Investment → Trigger** | 花园越长越美 → 舍不得离开 → 再次打开 | "Stored value increases likelihood of re-engagement" |

---

*本文档是 LAWA 项目从 RPG 化到养成式习惯引擎的完整设计规范。*
*所有代码实施以此文档为蓝本。*
*设计者：Ke & 达子 | 2026-06-13*

---

## 九、AI 能力增强设计（养成式核心差异）

### 9.1 AI 角色总览

| AI 角色 | 所属引擎 | 做什么 | 学术依据 |
|---------|----------|--------|----------|
| **信息流管家** | Trigger Engine | 跨 session 记忆 + 内容关联推送 | Ding et al. (2022): 个性化推送打开率提升3-5x |
| **隐形教练** | Action Engine | 行为感知 + 零打扰介入 | Aleven et al. (2017): AI"何时介入"比"如何介入"更重要 |
| **花园园丁** | Investment Engine | 模式发现 + 叙事化呈现 | Ebbinghaus (1885)/Anki: 间隔重复 + Nation (2001): 词汇8-12次复现 |
| **奖励设计师** | Reward Engine | 不可预测关联惊喜生成 | Castells et al. (2015): 推荐系统"惊喜度"提升满意度 |
| **沉默观察者** | 全引擎 | 知道何时不介入 | Fogg (2009): 行为=动机×能力×触发，触发不足时介入适得其反 |

### 9.2 AI 核心能力：跨 session 记忆

```
设计目标：
  用户今天打开 LAWA，AI 记得：
  - 昨天看了什么内容
  - 查过哪几个词
  - 跟同伴聊了什么话题
  - 哪篇内容读得吃力、哪篇读得顺畅

实现方式：
  - 每个用户的"语义记忆向量"（非存储对话原文，而是提取关键词/主题/难度）
  - 每日会话结束时压缩为语义摘要
  - 下次打开时，Trigger Engine 查询语义摘要 → 选择关联内容

设计原则：
  - 记忆窗口：7天滑动窗口（太短的记忆没用，太长的隐私负担重）
  - 遗忘机制：超过30天未出现的兴趣主题自动衰减
  - 隐私边界：不存储原始对话内容，只存储"用户对X主题感兴趣、Y难度水平"
```

### 9.3 AI 介入策略：Fogg 行为模型的实时应用

```
Fogg 公式：行为 = 动机 × 能力 × 触发

AI 的实时判断：
  用户读完一条资讯后：
  - 如果读得顺畅（高能力）→ 触发"跟读"建议（提高动机）
  - 如果读得吃力（低能力）→ 触发"显示中文"（提高能力）
  - 如果读了又放弃（低动机）→ 换一条更简单/更有趣的内容（提高动机）
  - 如果直接关闭（无触发）→ 不介入，尊重用户

沉默规则（按优先级）：
  1. 用户在流畅阅读中 → 不说话（心流保护）
  2. 用户读完直接关闭 → 不说话（尊重用户节奏）
  3. 用户连续跳过3次推送 → 降低推送频率（自适应）
  4. 用户一天未打开 → 无责备推送（零负罪感）
```

### 9.4 AI 可变奖励生成：不可预测的关联惊喜

```
奖励类型生成逻辑：
  1. 词汇复现奖励
     条件：用户今天遇到的词是"过去7天学过但最近2天未出现"的
     触发：AI 检测到复现 → "🎉 这个词你上周学过！还记得吗？"
     依据：Ebbinghaus 遗忘曲线 + Nation 词汇复现理论

  2. 理解突破奖励
     条件：用户今天读了一篇内容，其主题与3天前读过的某篇相关
     触发：AI 检测到主题关联 → "💡 上次你读这篇的时候理解了60%，
           今天关联的内容你理解了78%，进步了！"
     依据：Schmidt (1990) 注意假说 + Vygotsky 最近发展区

  3. 兴趣模式奖励
     条件：用户连续3天读了同一主题的内容
     触发：AI 检测到模式 → "🌱 我注意到你最近对XX感兴趣。
           你的兴趣词汇已经达到XX个，够读这篇完整文章了"
     依据：内在动机理论 (Deci & Ryan, 2000)

  4. 跨语言彩蛋
     条件：用户学的某个词在其他语言中有同源/相关词
     触发：AI 查询词源数据库 → "🍣 这个词来自XX语，你猜到了吗？"
     依据：文化语言学 + 跨语言迁移理论
```

### 9.5 AI 能力分阶段实施

| 阶段 | AI 能力 | 复杂度 | 前置依赖 |
|------|---------|--------|----------|
| **MVP (S1-S2)** | 基础推送 + 简单关联 | 低 | 词汇服务 |
| **S3** | 跨 session 记忆（7天滑动窗口） | 中 | 用户会话日志 |
| **S4** | 兴趣模式检测 + 成长洞察 | 中 | 记忆系统 |
| **S5-S6** | 可变奖励智能生成 | 高 | 模式检测 |
| **Post-MVP** | 沉默策略学习（强化学习） | 高 | 行为数据积累 |

---

## 附录A：理论参考文献

### 习惯形成理论
1. **Eyal, N.** (2014). *Hooked: How to Build Habit-Forming Products*. Portfolio.
   - 核心：Trigger → Action → Variable Reward → Investment 四步循环
   - 应用：整个 LAWA 养成引擎的框架基础

2. **Fogg, B.J.** (2009). "A Behavior Model for Persuasive Design". *Proceedings of Persuasive Technology*.
   - 核心：B = MAP（行为 = 动机 × 能力 × 触发）
   - 应用：AI 介入策略设计、沉默原则

3. **Hamari, J., Koivisto, J., & Sarsa, H.** (2014). "Does Gamification Work? – A Literature Review". *Proceedings of HICSS*.
   - 核心：游戏化短期有效但长期衰减
   - 应用：拒绝 RPG 化，选择养成式

### 第二语言习得理论
4. **Krashen, S.D.** (1985). *The Input Hypothesis: Issues and Implications*. Longman.
   - 核心：可理解输入 (i+1) + 情感过滤假说
   - 应用：信息流难度适配（90% 可理解 + 10% 略难）、零挫败保障

5. **Nation, I.S.P.** (2001). *Learning Vocabulary in Another Language*. Cambridge.
   - 核心：词汇需要 8-12 次有意义重复才能掌握
   - 应用：AI 跨 session 词汇复现机制

6. **Schmidt, R.** (1990). "The Role of Consciousness in Second Language Learning". *Applied Linguistics*, 11(2).
   - 核心：注意假说（Noticing Hypothesis）
   - 应用：可变奖励中的"🎉 这个词又出现了"设计

7. **Swain, M.** (1985). "Communicative Competence: Some Roles of Comprehensible Input and Comprehensible Output".
   - 核心：输出假说（说/写促进习得）
   - 应用：跟读/写一句等微输出行为

### 自适应 AI 与学习系统
8. **Aleven, V., et al.** (2017). "Instruction Based on Adaptive Learning Technologies". In *Handbook of Research on Learning and Instruction*.
   - 核心：AI 在"何时介入"比"如何介入"更重要
   - 应用：沉默观察者原则、行为感知触发

9. **Settles, B., & Meeder, B.** (2016). "A Trainable Spaced Repetition Model for Language Learning". *Proceedings of ACL*.
   - 核心：Duolingo 的间隔重复模型（Half-Life Regression）
   - 应用：词汇复现时间优化

10. **Settles, B., et al.** (2018). "A Deep Learning Approach to Spaced Repetition". *Proceedings of AIED*.
    - 核心：深度学习预测遗忘曲线，优化复习时机
    - 应用：跨 session 记忆系统中的复现时机决策

### 推荐系统与个性化
11. **Ding, Y., et al.** (2022). "Personalized Push Notifications: A Survey". *ACM Computing Surveys*.
    - 核心：个性化推送打开率比通用推送高 3-5 倍
    - 应用：Trigger Engine 个性化推送策略

12. **Castells, P., et al.** (2015). "Novelty and Diversity in Recommender Systems". In *Recommender Systems Handbook*.
    - 核心：推荐系统的"惊喜度"（Serendipity）提升用户满意度
    - 应用：Variable Reward 不可预测性设计

### 心理学与行为设计
13. **Deci, E.L., & Ryan, R.M.** (2000). "Self-Determination Theory". *Psychological Inquiry*.
    - 核心：内在动机三要素（自主/胜任/关联）
    - 应用：习惯引擎的内在动机设计

14. **Ebbinghaus, H.** (1885). *Über das Gedächtnis*.
    - 核心：遗忘曲线 → 间隔重复
    - 应用：词汇复现时间点优化

---

*本文档是 LAWA 项目从 RPG 化到养成式习惯引擎的完整设计规范。*
*所有代码实施以此文档为蓝本。*
*学术依据版本：v2（包含14篇参考文献的理论支撑）*
*设计者：Ke & 达子 | 2026-06-13*

---

## 十、UI 界面设计规范

### 10.1 设计语言："最简洁、最灵幻"

**核心审美：极简禅意 × 数字灵幻**

```
配色体系：
  🎨 主色：#667eea (LAWA紫) → 渐变为 #764ba2
  🎨 背景：#f8f9ff (极浅紫白) / #0a0a1a (深空色)
  🎨 文字：#1a1a2e (深紫黑) / #e8e8ff (浅紫白)
  🎨 强调：#00d4aa (翠绿) — 成长/奖励/正向
  🎨 点缀：#ff6b9d (樱花粉) — 惊喜/彩蛋
  
设计原则：
  ✦ 留白 > 内容 — 每个页面至少 40% 空白
  ✦ 动效 > 静态 — 微交互动效（漂浮/渐变/呼吸光）
  ✦ 圆形 > 直角 — 圆角 16px+，无尖锐元素
  ✦ 文字少到不能再少 — 能用图标不用字，能用emoji不用图标
  ✦ 透明质感 — glassmorphism 背景模糊效果

字体：
  - 中文：Noto Sans SC / 系统默认
  - 英文：Inter / system-ui
  - 字号：主内容 15px，标题 24-32px，微文本 12px
  - 行高：1.8（舒适阅读间距）

动效风格：
  - 页面切换：渐变淡入（0.3s ease）
  - 卡片出现：从底部滑入（0.4s ease-out）
  - 按钮悬停：轻微上浮（translateY(-2px)）+ 阴影渐变
  - 语言花园：粒子飘动效果（CSS @keyframes）
  - 奖励触发：中心爆裂扩散 + 微音效
```

### 10.2 登录页设计（微信扫码优先）

```
页面结构（极简）：

┌─────────────────────────────────────┐
│                                     │
│              🦝 LAWA                │
│                                     │
│        你的语言习惯花园              │
│                                     │
│     ┌─────────────────────┐          │
│     │                     │          │
│     │    [微信二维码]      │          │
│     │                     │          │
│     └─────────────────────┘          │
│                                     │
│         扫码登录 / 注册              │
│                                     │
│   ─── 或 ───                        │
│                                     │
│    邮箱/账号登录 →                  │
│                                     │
│    © LAWA · 隐私政策 · 用户协议      │
│                                     │
└─────────────────────────────────────┘

设计要点：
  - 背景：深空紫渐变 + 缓慢漂浮的光点粒子（CSS particle animation）
  - 二维码居中，轻微呼吸动画（box-shadow 脉动）
  - 下方小字"扫码登录 / 注册"，点击可切换为手机号登录
  - "邮箱/账号登录"为次要入口，轻量文字链接
  - 底部法律声明极小字号（10px），半透明
  - 无注册页——扫码即注册，首次登录自动创建账号
  - 无忘记密码——微信登录天然解决
```

### 10.3 主界面：仪表盘（信息流首页）

```
布局（单列滚动，无侧边栏）：

┌─────────────────────────────────────┐
│  🦝 LAWA     ☀️ 早安, Ke    ⚙️    │
│  ─────────────────────────────────  │
│                                     │
│  ┌─ 今日花园 ──────────────────┐   │
│  │ 🌱🌿🌼🌱🌿🌻🌱🌿🌼🌱   │   │
│  │ 236 棵植物 · 3 株开花       │   │
│  │ 连续 7 天 🔥                 │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 资讯卡片 ──────────────────┐   │
│  │ 📰 AI learns to write poetry │   │
│  │ 45秒 · 难度 🌟🌟             │   │
│  │ 有个词不认识？→ 点我         │   │
│  │ [跟读] [收藏] [换一条]        │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 花园日记 ──────────────────┐   │
│  │ 🌙 晚间回顾                  │   │
│  │ 今日新词：3 · 跟读：1次      │   │
│  │ "metaphor" → 种子→幼苗 🌱   │   │
│  └──────────────────────────────┘   │
│                                     │
│  [导航栏：🏠花园 📖词汇 👤我]     │
└─────────────────────────────────────┘

设计要点：
  - 底部 tab 导航（3-4个 tab），替代侧边栏
  - 顶部：日期问候 + 设置齿轮（右上角）
  - 信息流为纵向滚动卡片，每张卡片一个"微行为"入口
  - 卡片圆角 20px，白色背景 + 微妙阴影
  - 花园状态条在顶部，实时更新
  - 无多余的导航/面包屑/功能按钮
```

### 10.4 语言花园页面

```
┌─────────────────────────────────────┐
│  ← 花园           🌱 种子 12       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │                             │   │
│  │     🌱 🌿 🌼 🌱           │   │
│  │   🌱 🌿🌻🌱 🌿            │   │
│  │     🌿 🌼 🌱 🌿🌻         │   │
│  │                             │   │
│  │   词汇花园 · 236 棵植物     │   │
│  │   种子 12 · 发芽 89 · ...   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─ 最近开花 ─────────────────┐   │
│  │ 🌼 "metaphor" — 昨天开花   │   │
│  │ 🌼 "paradigm" — 3天前开花  │   │
│  └──────────────────────────────┘   │
│                                     │
│  [花园] [词汇] [日记] [洞察]        │
└─────────────────────────────────────┘

设计要点：
  - 花园用 CSS 网格展示"植物"，每棵植物大小/颜色/动画不同
  - 种子=小灰点，发芽=小绿芽，开花=彩色花朵 emoji + 粒子
  - 点击植物 → 弹出词汇详情
  - 下方 tab 切换花园不同视角
  - 整个页面背景从深蓝渐变到翠绿（模拟从地下到地面）
```

### 10.5 微信扫码登录实现方案

```
技术方案选择（两种，按优先级）:

方案A：微信公众号/开放平台 OAuth（推荐）
  流程：
    1. 用户打开 LAWA → 显示微信二维码
    2. 用户扫码 → 微信回调 → 获取 openid
    3. 后端用 openid 查询/创建用户 → 返回 JWT token
    4. 前端存储 token → 跳转仪表盘

  需要：
    - 微信公众号（服务号）或微信开放平台账号
    - 配置回调域名
    - 后端实现：/api/v1/auth/wechat/login (POST)
    - 前端：qrcode.js 生成二维码 + 轮询扫码状态

  后端 API 设计：
    POST /api/v1/auth/wechat/qrcode
      → 返回 { qrcode_url, scene_id }
    
    GET /api/v1/auth/wechat/status?scene_id=xxx
      → 轮询扫码状态：{ status: 'waiting'|'scanned'|'confirmed', token?: str }
    
    GET /api/v1/auth/wechat/callback?code=xxx&state=xxx
      → 微信回调处理

方案B：微信小程序扫码（备选）
  流程：
    1. 用户生成小程序码
    2. 微信扫码 → 打开小程序 → 授权登录
    3. 小程序向服务端换取 token
    4. token 传递给 Web 端（通过 URL scheme 或 short link）

  更复杂，需要额外开发小程序

方案C：简易 MVP 方案（先跑起来）
  流程：
    1. 后端生成一次性登录码（6位数字+字母）
    2. 前端展示登录码 + 模拟微信扫码（实际输入码）
    3. 用户在任何设备输入码 → 登录
    4. 后续升级为真实微信 OAuth

  适合 Sprint 1 快速验证，后续迁移到方案A

前端实现（方案A）：
  <template>
    <div class="wechat-login">
      <canvas ref="qrcode"></canvas>
      <p v-if="status === 'waiting'">请使用微信扫码</p>
      <p v-else-if="status === 'scanned'">✅ 已扫码，请在手机上确认</p>
      <p v-else-if="status === 'confirmed'">🎉 登录成功，正在跳转...</p>
    </div>
  </template>

  onMounted(() => {
    // 1. 请求二维码
    api.post('/auth/wechat/qrcode').then(res => {
      QRCode.toCanvas(canvas.value, res.data.qrcode_url)
      sceneId = res.data.scene_id
    })
    // 2. 轮询扫码状态
    pollTimer = setInterval(async () => {
      const res = await api.get(`/auth/wechat/status?scene_id=${sceneId}`)
      if (res.data.status === 'confirmed') {
        localStorage.setItem('lawa_token', res.data.token)
        router.push('/dashboard')
      }
    }, 2000)
  })
```

### 10.6 路由结构改造（去 RPG 化）

```
旧路由 → 新路由映射：
  /login          → 保留，改为微信扫码优先
  /register       → 删除（扫码即注册）
  /dashboard      → 改为 /garden（信息流首页）
  /assessment     → 保留
  /world          → 删除（RPG世界地图）
  /guild          → 改为 /circles（兴趣圈）
  /shop           → 改为 /trophies（奖杯柜）
  /coin           → 删除（合并到 profile）
  /leaderboard    → 删除（去排行榜）
  /match          → 保留，改造为"语伴匹配"
  /achievements   → 保留，改造为"里程碑"
  /events         → 删除（合并到信息流）
  /plan           → 保留
  /tasks          → 保留，改造为"微习惯"
  /tutor          → 保留
  /companion      → 保留
  /vocabulary     → 改为 /garden/words（花园的词汇视图）
  
新路由（新增）：
  /garden         — 语言花园首页（原 dashboard 改造）
  /garden/words   — 词汇视图（原 vocabulary）
  /garden/insight — 成长洞察
  /trophies       — 奖杯柜（原 shop）
  /circles        — 兴趣圈（原 guild）
  
最终路由数量：从 25 条 → 约 16 条（精简 36%）
```

### 10.7 前端组件重构计划

```
保留改造：
  TutorChat.vue        → 保留，UI 改为灵幻风格
  TutorChatWidget.vue  → 保留，右下角浮动气泡
  TutorInsights.vue    → 改造为 /garden/insight 组件
  TutorLesson.vue      → 保留，改造为"资讯卡片"样式
  TutorMarket.vue      → 删除（RPG任务市场）
  TutorProfile.vue     → 改造，与信息流整合

新增组件：
  InfoFeedCard.vue     — 信息流卡片（核心组件）
  GardenView.vue       — 语言花园可视化
  GardenPlant.vue      — 单棵"植物"组件
  WechatLogin.vue      — 微信扫码登录
  BottomNav.vue        — 底部导航栏
  InsightPanel.vue     — 成长洞察面板
  TrophyCabinet.vue    — 奖杯柜
  CircleCard.vue       — 兴趣圈卡片

删除组件：
  - 所有 RPG 相关组件（WorldMap, Guild, Shop, Coin, Leaderboard, Events）
```

---

## 附录B：设计原则总结（一目了然）

```
旧 LAWA（RPG 化）            → 新 LAWA（养成式习惯引擎）
────────────────────────────────────────────────────
🎮 游戏化                     → 🌿 习惯养成
📊 排行榜                     → 🌱 自我成长
⚔️ 公会/竞争                 → 🌸 兴趣圈/陪伴
🏪 商店/装备                 → 🏆 奖杯/纪念
🗺️ 世界地图                  → 🖼️ 语言花园
💰 金币经济                   → 📈 成长积分
📋 任务/副本                 → 📰 信息流/微行为
👤 职业/等级                 → 🌳 语言生命阶段
🔐 用户名密码登录             → 📱 微信扫码登录
🎨 紫色渐变（现代风）         → ✨ 深空灵幻（极简风）
📱 侧边栏导航                 → 📱 底部 tab 导航
```

---

*本文档是 LAWA 项目从 RPG 化到养成式习惯引擎的完整设计规范。*
*所有代码实施以此文档为蓝本。*
*学术依据版本：v2（包含14篇参考文献的理论支撑）*
*设计版本：v3（新增 UI/UX 规范 + 微信扫码登录）*
*设计者：Ke & 达子 | 2026-06-13*
