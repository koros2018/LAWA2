#!/bin/bash
# LAWA2 数据备份脚本
# 用法: ./scripts/backup.sh
# 建议配合 cron 每天执行一次

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_FILE="$PROJECT_DIR/lawa2.db"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/lawa2_${TIMESTAMP}.db"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 复制数据库文件
cp "$DB_FILE" "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"

echo "✅ 备份完成: ${BACKUP_FILE}.gz ($(du -h "${BACKUP_FILE}.gz" | cut -f1))"

# 清理旧备份（保留最近 N 天）
find "$BACKUP_DIR" -name "lawa2_*.db.gz" -mtime +$RETENTION_DAYS -delete
echo "🧹 已清理 $RETENTION_DAYS 天前的旧备份"

# 显示最近 5 个备份
echo "📦 最近备份:"
ls -lt "$BACKUP_DIR"/lawa2_*.db.gz 2>/dev/null | head -5
