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
| rick-dev | 个人项目标准开发与发布流程：三道闸门、双发布路线（Docker/exe）、验收清单，附填空式工作手册模板 | [skills/rick-dev](skills/rick-dev/) |

> 索引由 `rick-skill-pub` 在每次发布时自动维护。
