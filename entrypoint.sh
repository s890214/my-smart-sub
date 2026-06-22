#!/bin/bash

# 切换到程序可能存在的工作目录
cd /base 2>/dev/null || cd /app 2>/dev/null

# 1. 启动原版 subconverter（后台，25500 端口）
if [ -f "./subconverter" ]; then
    ./subconverter &
else
    subconverter &
fi

# 等待 subconverter 启动完成（最多等 10 秒）
echo "[小跟班提示] 等待 subconverter 启动..."
for i in {1..20}; do
    if curl -s http://127.0.0.1:25500 >/dev/null 2>&1; then
        echo "[小跟班提示] subconverter 已就绪"
        break
    fi
    sleep 0.5
done

# 2. 启动 Python 智能合并服务（25501 端口）
echo "[小跟班提示] 启动智能合并服务..."
python3 /base/wrapper.py
