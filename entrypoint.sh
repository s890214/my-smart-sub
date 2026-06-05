#!/bin/bash

# 1. 让原版的 subconverter 二进制程序在后台秘密启动，并把端口改成 25501
if [ -f "/base/subconverter" ]; then
    /base/subconverter -l 127.0.0.1:25501 &
else
    subconverter -l 127.0.0.1:25501 &
fi

# 2. 启动我们刚刚写好的 Python 小跟班，占领对外公开的 25500 端口
python3 /base/wrapper.py