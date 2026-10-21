# my-smart-sub

Subconverter 的智能合并包装层：在 subconverter 转换结果的基础上，按 `server:port` 匹配原始订阅节点，保留原始节点的完整字段，仅替换节点名称，并把原始订阅中的 DNS 配置透传到输出。

## 上游与许可证

- 基础镜像：`asdlokj1qpi23/subconverter`，上游项目为 [tindy2013/subconverter](https://github.com/tindy2013/subconverter)，许可证 **GPL-3.0**。
- 本仓库的 `wrapper.py`、`entrypoint.sh`、`Dockerfile` 属于该 GPL-3.0 作品的衍生部分，整体以 **GPL-3.0** 发布，全文见 [LICENSE](LICENSE)。
- 镜像分发同时提供完整构建源码：本仓库（`Dockerfile` + 脚本）与上述上游项目源码。任何人都可以据此重建镜像。

## 构建

```bash
docker build -t my-smart-sub .
```

## 运行

```bash
docker run -d --name my-smart-sub -p 25500:25500 my-smart-sub
```

容器内 `25500` 为 subconverter 原始端口，`25501` 为包装层端口。对外提供服务的入口在 `entrypoint.sh` 中定义。
