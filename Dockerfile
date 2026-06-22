# 1. 基础镜像直接使用优化版镜像
FROM asdlokj1qpi23/subconverter:latest

# 2. 接收构建参数
ARG VERSION=unknown

# 3. 安装 Python3、PyYAML 和 Bash
RUN apk add --no-cache python3 py3-yaml bash

# 4. 复制脚本到容器
COPY wrapper.py /base/wrapper.py
COPY entrypoint.sh /base/entrypoint.sh

# 5. 创建 VERSION 文件（使用构建参数）
RUN echo "$VERSION" > /base/VERSION

# 4. 赋予可执行权限
RUN chmod +x /base/entrypoint.sh

# 5. 声明对外暴露标准 25500 端口
EXPOSE 25500

# 6. 运行引导脚本
ENTRYPOINT ["/bin/bash", "/base/entrypoint.sh"]
