# LAWA2 部署文档

> 版本：v3.8.0 | 更新日期：2026-06-18

---

## 系统要求

### 后端
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (可选，用于前端构建)

### 前端
- Node.js 18+
- npm 或 yarn

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/koros2018/LAWA2.git
cd LAWA2
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lawa2
DB_USER=postgres
DB_PASSWORD=your_password

# API
API_PORT=6290
CORS_ORIGINS=http://localhost:6292

# LLM
LLM_PROVIDER=sensenova
SENSENOVA_API_KEY=your_key
```

### 3. 启动后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn src.main:app --host 0.0.0.0 --port 6290 --reload
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev -- --port 6292
```

### 5. 访问应用

- 前端：http://localhost:6292
- 后端 API：http://localhost:6290
- API 文档：http://localhost:6290/docs

---

## 生产部署

### Docker 部署

```bash
# 构建镜像
docker build -t lawa2:latest .

# 运行容器
docker run -d \
  -p 6290:6290 \
  -p 6292:6292 \
  -e DB_HOST=db \
  -e DB_PASSWORD=your_password \
  --name lawa2 \
  lawa2:latest
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

---

## 数据库迁移

```bash
# 创建数据库
psql -U postgres -c "CREATE DATABASE lawa2;"

# 运行迁移
python src/database/migrate.py
```

---

## 日志查看

```bash
# 查看后端日志
tail -f logs/app.log

# 查看前端构建日志
tail -f frontend/build.log
```

---

## 故障排查

### 后端无法启动

1. 检查端口 6290 是否被占用
2. 检查数据库连接配置
3. 查看日志：`logs/app.log`

### 前端无法启动

1. 检查 Node.js 版本 (>= 18)
2. 删除 node_modules 重新安装：`rm -rf node_modules && npm install`
3. 检查端口 6292 是否被占用

### API 返回 500 错误

1. 检查后端日志
2. 确认数据库连接正常
3. 验证环境变量配置

---

## 备份与恢复

### 备份数据库

```bash
pg_dump -U postgres lawa2 > lawa2_backup.sql
```

### 恢复数据库

```bash
psql -U postgres lawa2 < lawa2_backup.sql
```

---

## 监控

### 健康检查

```bash
curl http://localhost:6290/health
```

### 查看统计

```bash
curl http://localhost:6290/api/v2/admin/stats
```

---

*文档维护：Ke & 达子 | 2026-06-18*
