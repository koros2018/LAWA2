# LAWA2 — 养成式语言习惯引擎

## 项目结构

```
LAWA2/
├── src/
│   ├── engine/        # 核心引擎（Action / Reward / Trigger / Investment）
│   │   ├── __init__.py
│   │   ├── action_engine.py
│   │   ├── reward_engine.py
│   │   ├── trigger_engine.py
│   │   └── investment_engine.py
│   ├── models/        # 数据模型
│   │   ├── __init__.py
│   │   ├── habit.py        # 习惯引擎数据模型
│   │   └── user.py         # 用户模型
│   ├── routes/        # API 路由
│   │   ├── __init__.py
│   │   └── habit.py        # 习惯 API
│   ├── database/      # 数据库
│   │   └── main.py
│   ├── services/      # 服务层
│   ├── agent/         # AI Agent
│   └── config.py      # 配置
├── frontend/          # Vue3 前端（新建）
├── tests/             # 测试
├── docs/              # 设计文档
└── memory/            # 项目日志
```

## 快速开始

```bash
pip install -r requirements.txt
python -m src.database.main  # 初始化数据库
python -m src.routes.main    # 启动 API
```

## 核心概念

- **微行为**（Micro-Habit）：< 30 秒的学习行为
- **可变奖励**（Variable Reward）：不可预测的正向反馈
- **语言花园**（Language Garden）：词汇生命周期可视化
- **信息流**（Info Feed）：嵌入日常生活的学习内容
