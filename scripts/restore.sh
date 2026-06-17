#!/bin/bash
# LAWA2 数据恢复脚本
# 用法: ./scripts/restore.sh <backup_file.db.gz>
# 例如: ./scripts/restore.sh backups/lawa2_20260617_170021.db.gz

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_FILE="$1"
DB_FILE="$PROJECT_DIR/lawa2.db"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ 用法: ./scripts/restore.sh <backup_file.db.gz>"
    echo ""
    echo "可用备份:"
    ls -lt "$PROJECT_DIR/backups/lawa2_*.db.gz" 2>/dev/null | head -10
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 确认
read -p "⚠️  恢复将覆盖当前数据库，继续？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

# 停止后端服务
pkill -f 'uvicorn.*main:app' 2>/dev/null || true
sleep 2

# 解压并恢复
gunzip -c "$BACKUP_FILE" > "$DB_FILE"

echo "✅ 恢复完成: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"
echo "💡 请手动重启后端: cd $PROJECT_DIR && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 6290 &"
