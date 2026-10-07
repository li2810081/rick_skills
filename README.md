# rick_skills

Rick 的个人 Agent Skills 公共仓库（personal, public agent skills）。

## 安全门禁（硬性）

本仓库禁止一切 API 密钥、令牌、私钥、凭证入库：

- 已开启 GitHub Secret Scanning + Push Protection，命中即被 GitHub 拒收。
- 发布前必须通过 `rick-skill-pub` 技能的本地三道扫描：文件名黑名单、已知令牌正则、硬编码赋值扫描。
- 任何疑似命中：只允许报告「文件 + 行号 + 风险类型」，禁止展示内容本身；必须先脱敏，重扫通过后才能发布。
- 禁止 force push、禁止改写历史。

## 技能索引

| 技能 | 用途 | 路径 |
| --- | --- | --- |
| rick-skill-pub | 把任意技能通过安全门禁发布到本仓库的发布器 | [skills/rick-skill-pub](skills/rick-skill-pub/) |
| rick-dev | 个人项目开发与发布流程：实际连接隔离检查、风险分层、保留业务数据的回滚、分阶段验收、项目事实模板及工程参考索引 | [skills/rick-dev](skills/rick-dev/) |
| gm030-agent-dev | 多 Agent 开发编排：Codex 设计、ZCode 实现、Hermes 调度验收；七步循环、防重复派发、超时与恢复核对、可选 worktree 并行 | [skills/gm030-agent-dev](skills/gm030-agent-dev/) |
| nsis-pack | NSIS 封包能力：把任意 Windows 应用构建产物（来源不限）封装成专业安装包——安装/升级覆盖/卸载/快捷方式/静默安装/版本元数据，模板真机验证全链路通过，附发布仪式与 13 条实战踩坑 | [skills/nsis-pack](skills/nsis-pack/) |

> 索引由 `rick-skill-pub` 在每次发布时自动维护。
