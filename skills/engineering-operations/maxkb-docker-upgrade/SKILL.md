---
name: maxkb-docker-upgrade
description: Use when upgrading an existing Docker-deployed MaxKB instance, including deployment discovery, release compatibility checks, backups, container replacement, migration verification, and rollback planning. Excludes fresh installations and unrelated Docker maintenance.
---

# MaxKB Docker 升级

通用流程见 [Docker 应用升级](../docker-app-upgrade/SKILL.md)。本入口提供 MaxKB 的版本、数据和验收细节。

将现有实例升级到用户指定版本或执行时核实的官方最新稳定版，保留数据和部署配置，明确技术验收与业务验收的范围。适用于 Docker run 和 Compose；不假设目标一定在本机。

## MaxKB 专用检查

按上面的通用流程执行，在对应步骤补充以下检查。

- **版本与迁移路径**。V2 可请求实际服务地址的 /admin/api/profile，读取 JSON 中的 data.version 和 data.edition。反向代理可能返回 HTTP 200 的 HTML，须检查响应内容。从官方更新日志核对目标版本、版本类型和模型供应商兼容变化。V1 到 V2 应按迁移工具文档准备所需版本与空目标环境。
- **数据与备份**。V2 一体化镜像重点检查 /opt/maxkb，同时盘点实例的其他挂载、外部数据库和对象存储。按实际库名和角色执行 pg_dump，不能假定角色是 postgres。Windows 下可在容器内用 -Fc -f 生成二进制备份，再用 docker cp 复制。核对备份退出码、可读性和恢复条件。
- **停机一致性**。确认内置 PostgreSQL 已退出，再复制物理数据。docker stop 超时后可能强制结束进程，单凭容器已停止不足以证明数据库优雅退出。
- **验收**。记录用户、智能体、知识库数量，确认表名后查询。重建后核对数据库迁移、缓存和工作进程、版本接口、管理页及业务数量，有条件时再验证登录、模型调用和代表性智能体。发生数据库迁移后按通用流程从升级前数据回退。

## 已验证经验与来源

本技能由用户确认的 2026-11-04 MaxKB 升级会话整理，不依赖 Beacon 服务或记忆 ID。

- 案例是 V2 社区版从 `v2.10.1-lts` 升至 `v2.10.8-lts`，复用了匿名数据卷和原端口；迁移日志成功、版本接口确认、管理页面 HTTP 200，用户/智能体/知识库数量前后一致。
- 当时未验证登录后的模型调用或智能体执行，也未做备份恢复演练；不得将这些项目写成已经验证。
- 旧服务停止后，新版数据库进行了自动恢复；因此后续流程增加数据库退出状态与备份可恢复性检查，该改进并非本次已完成的恢复测试。

执行时重新核实官方资料：

- [更新日志](https://docs.fit2cloud.com/maxkb/changelog/)
- [在线部署与升级](https://docs.fit2cloud.com/maxkb/installation/online_installtion/)
- [迁移工具](https://docs.fit2cloud.com/maxkb/installation/migrate/)
