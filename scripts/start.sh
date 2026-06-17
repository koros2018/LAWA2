#!/bin/bash
# LAWA2 后端启动脚本
cd /mnt/d/OpenClawData2workspace/Projects/LAWA2
python3 -m uvicorn main:app --host 0.0.0.0 --port 6290 > /tmp/lawa2_backend.log 2>&1 &
echo $!
sleep 5
curl -s http://localhost:6290/health
