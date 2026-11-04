---
name: docker-app-upgrade
description: Use when upgrading an existing Docker run or Compose application to a target image while preserving its configuration and persistent data, or rehearsing the replacement in isolation.
---

# Docker 应用升级

1. 用 docker context show、docker ps -a 和 docker inspect 核实目标、运行状态、原镜像 ID、挂载、端口、网络、重启策略及自定义配置。Compose 以实际项目和覆盖文件为准。保护配置中的凭据。
2. 根据应用官方升级说明核实版本跨度、数据库迁移条件、必要中间版本和支持的备份方式。识别卷、绑定目录、外部数据库及可写层中的业务数据。信息不足时暂停切换。
3. 停机前拉取目标镜像，记录实际摘要。latest 是可变标签，比较镜像 ID 决定是否需要重建。测试请求优先用独立卷、独立容器名和本机临时端口演练，隔离外部连接。
4. 记录业务基线，停止写入，备份数据和配置并验证备份可读。数据库按应用支持的方式导出或一致性快照。备份失败则恢复原服务。无状态应用可在确认无持久数据后跳过数据备份。
5. 通过原部署方式替换镜像，保留必要参数并显式复用命名卷、匿名卷或绑定目录。只允许一个写入实例。按项目和服务限定 Compose 操作。保留旧镜像并防止旧容器自动启动。
6. 核对实际镜像 ID、应用版本、健康状态、迁移日志、访问端点和代表性数据。区分挂载探针、应用可用性和登录后的业务测试。记录已验证范围、备份位置和回退条件。
7. 新版尚未写入时可恢复旧配置和镜像。发生迁移后，先停止新版，用独立卷及匹配的外部存储恢复升级前状态，再验证旧版。保留升级后写入，确认数据处理方式后切换。
