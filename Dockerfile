# 1. 基础镜像直接使用你现在指定的这个优化版镜像
FROM asdlokj1qpi23/subconverter:latest

# 2. 镜像内部默认没有 Python，我们需要帮小跟班安装 Python3 和 Bash 环境
RUN apk add --no-cache python3 bash

# 3. 把我们在服务器上写好的两个脚本文件，复制进容器内部的 /base/ 目录里
COPY wrapper.py /base/wrapper.py
COPY entrypoint.sh /base/entrypoint.sh

# 4. 给引导脚本赋予可执行权限
RUN chmod +x /base/entrypoint.sh

# 5. 声明对外暴露原厂标准的 25500 端口
EXPOSE 25500

# 6. 让容器启动时，不再运行老程序，而是运行我们的引导脚本
ENTRYPOINT ["/bin/bash", "/base/entrypoint.sh"]