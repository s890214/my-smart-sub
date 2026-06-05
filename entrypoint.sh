#!/bin/bash

# 1. 启动前，用 sed 命令把 subconverter 的配置文件端口强行改成 25501
# 这样它就不会跟我们对外的 25500 端口抢位置了
if [ -f "/base/pref.toml" ]; then
    sed -i 's/port = 25500/port = 25501/g' /base/pref.toml
    sed -i 's/port=25500/port=25501/g' /base/pref.toml
fi

if [ -f "/base/pref.ini" ]; then
    sed -i 's/port = 25500/port = 25501/g' /base/pref.ini
    sed -i 's/port=25500/port=25501/g' /base/pref.ini
fi

# 2. 让原版 subconverter 在后台启动（它会乖乖去听 25501 端口）
if [ -f "/base/subconverter" ]; then
    /base/subconverter &
else
    subconverter &
fi

# 3. 启动 Python 小跟班，顺利占领对外的 25500 端口
python3 /base/wrapper.py