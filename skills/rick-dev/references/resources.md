# 工程参考资料

索引整理日期：2026-10-06。外部仓库内容会变化；本文件标注用途，不保证链接中的实现始终适用于当前项目。只读取与当前任务相关的资料，不默认下载、运行模板或安装依赖。

## 主要参考

| 资料 | 何时查阅 | 重点借鉴 |
| --- | --- | --- |
| [FastAPI 官方全栈模板](https://github.com/fastapi/full-stack-fastapi-template) | 新建 FastAPI + React Web 项目，规划前后端、测试和 Compose 部署 | 项目结构、接口客户端生成、数据库迁移、环境配置、验证与发布的连接方式 |
| [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)（[中文版](https://github.com/zhanymkanov/fastapi-best-practices/blob/master/README_ZH.md)） | FastAPI 目录组织、异步调用、配置、后台任务、迁移及测试设计 | 作者的生产经验与取舍；其 AGENTS.md 可作为把工程约定写给 AI 的参考 |
| [uv 官方 Docker 示例](https://github.com/astral-sh/uv-docker-example) | Python 项目采用 uv，并构建 Docker 镜像 | 锁文件安装、构建缓存、构建与运行环境的组织；结合 [uv Docker 文档](https://docs.astral.sh/uv/guides/integration/docker/) 核对具体命令 |

## 补充参考

| 资料 | 何时查阅 | 重点借鉴 |
| --- | --- | --- |
| [Cookiecutter Django](https://github.com/cookiecutter/cookiecutter-django) | Django 项目接入生产配置，或比较已有生产模板的配套 | 开发/生产配置、Compose、测试及可选任务和错误监控集成；不因此要求项目采用 Django |
| [Agent Engineer](https://github.com/addyosmani/agent-engineer) | 改善 AI 接手体验及项目指令 | 任务上下文、验证与评审方法，以及 [AGENTS.md 写法](https://github.com/addyosmani/agent-engineer/tree/main/15-agents-md)；保留对本项目有用的事实，避免堆积泛化指令 |

## 采用方式

- 这些资料不是技术栈选择或部署授权。用户明确要求优先；已有项目沿用实际约束，迁移需有具体收益。
- 模板中附带的邮件、代理、队列等组件按需求选择，不把模板依赖全部变成项目默认依赖。
- 对本用户的项目，参考实现应适配已确认偏好：Python 使用 uv；服务优先以完整 Compose 在 1Panel/Docker 部署；环境配置使用 .env；AI 通过命令查日志，网页展示结果、可理解的错误说明及查询编号。这些偏好不要求已有项目立即迁移。
- 核对 .env 的 Compose 插值与容器变量传入方式；真实配置不入库、不打进镜像，参考模板的示例配置不能直接当生产配置。
- 采用代理或 HTTPS 配置前，确认与 1Panel 的职责及端口不冲突；已有数据库、网络和持久化目录按项目实际填写。
- 将选定做法、适用版本和验证命令落入项目事实或发布手册；外部链接不能替代可执行的本项目步骤。
