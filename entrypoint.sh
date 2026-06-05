#!/bin/bash

# 切换到程序可能存在的工作目录，确保原版能顺畅读取组件
cd /base 2>/dev/null || cd /app 2>/dev/null

# 1. 让原版 subconverter 在后台默认启动（它会使用它雷打不动的默认 25500 端口）
if [ -f "./subconverter" ]; then
    ./subconverter &
else
    subconverter &
fi

# 2. 启动 Python 小跟班（去听 25501 端口，不再跟原版抢位置）
python3 /base/wrapper.py