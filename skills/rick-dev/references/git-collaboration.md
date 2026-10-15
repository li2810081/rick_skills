# Git 协作：已核对的上游做法与本地采用边界

用于分支协作、PR、集成与检查配置；不要求每次普通任务读取。以下是原始资料与配置的观察，不是对本机集成已跑通的声明。

## 1. GitHub Flow：短期主题分支，审查后合入，及时收尾

来源：https://docs.github.com/en/get-started/using-github/github-flow

上游做法：每组无关改动分别开描述性分支；逻辑完整的提交；PR 说明问题和变更并关联 Issue；需要早期反馈时使用草稿 PR；审查后合入，完成后删除分支。

本地采用：按独立功能而非 Agent 名称划分分支，多个 BD 可以属于同一功能。跨 Agent 接手保留原分支。PR 提供范围、任务引用、验证和未验证项；远程写入与删除仍需授权。不强制纯本地仓库使用 GitHub。

## 2. Git 项目自身：小提交与临时组合验证

来源：https://github.com/git/git/blob/master/Documentation/gitworkflows.adoc

上游做法：把修改拆为可理解、逻辑完整的小步骤；主题分支隔离功能；多个主题的相互作用可先在一次性集成分支测试；阅读远程状态用 fetch，不把隐式合并的 pull 当只读刷新。该文明确指出其完整多层分支体系通常不适合小项目。

本地采用：避免混入无关重构；修复与必要回归测试通常保持为一个可理解的逻辑改动，不机械按文件拆提交。需要组合验证但暂不宜改稳定基线时，可建立明确可丢弃的验证分支；禁止其他开发以此分支为长期基线。它不同于承担真实功能交付的临时集成分支，必须标清用途。不得照搬 maint/next/seen 长期分支体系。获取远程后明确是否 merge/rebase，仍遵守授权和共享历史保护。

## 3. FastAPI 官方全栈模板：独立检查与可复查报告

已读取实际配置：
- https://github.com/fastapi/full-stack-fastapi-template/blob/master/.github/workflows/test-backend.yml
- https://github.com/fastapi/full-stack-fastapi-template/blob/master/.github/workflows/playwright.yml

观察：后端测试由 PR 和主干 push 触发，权限 contents:read、checkout 不保留凭据、有超时、保存覆盖率报告；浏览器测试有失败 trace、报告归档和一个用于分支保护的汇总 job。具体 job/依赖/版本均属于上游项目，不直接成为本项目默认。

本地采用：
- 配置已有 CI 时优先最小权限、确切版本证据、任务超时、失败日志/浏览器 trace，默认不授予生产权限；发布单独授权。
- 必需检查用明确稳定的 job 名称；条件执行、多 job 组合时核对 failed/cancelled/skipped/pending 的真实语义，不能“最后一步绿”就把之前失败隐藏。
- 不直接复制模板中的 docker compose down -v 等清理命令到现有机器；清理只能针对本轮独占隔离资源。
- 测试环境隔离须先证明，报告按敏感性审查，不上传密钥、客户数据或原始私有日志。
- 不照搬上游 90% 覆盖率、分片数、框架或工具版本；按项目风险和实际反馈耗时选择，普通任务不启动完整重型流水线。

## 4. GitHub merge queue：验证组合，而不是各自通过就合

来源：https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue

上游做法：结合最新目标分支和队列前序变更检查组合版本；GitHub Actions 须处理 merge_group 事件，否则缺少必需检查。功能受仓库类型及套餐限制。

本地采用：小团队先由集成负责人按序合入并验证，不先安装队列工具；高并发确有需要且仓库支持时再按授权启用。目标分支或待合入提交变动后，旧组合验证不能直接证明新组合通过。记录验证过的基线与候选 commit；合并后若代码与验证组合不一致则重验。

## 5. 版本对象：commit / branch / PR / tag / Release 各管什么

来源：https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases 、https://docs.docker.com/dhi/core-concepts/digests/

- Commit 是快照，Branch 是移动的线，PR 是一次改动的审查入口，Tag 是给某个 commit 贴的版本名，Release 是基于 Tag 的对外版本记录（说明+附件）。
- 一个版本可含多个 PR；PR 合并不自动产生 Tag/Release/部署，除非配置了自动化。线上实际跑什么查部署记录与运行信息，不能只看最新 Release。
- Docker 镜像以 digest（内容 SHA-256）为不可变身份，tag 可复用而 digest 不会；部署与验收优先绑定 digest/校验和。
- 分支保护规则（必需检查、禁止 force push）是仓库级强制，能否用取决于仓库类型与套餐；技能内的流程约定是 Agent 自律，不自动成为平台限制，两者都要有但不互相替代。

## 采用原则

复用原则，不搬整套流程；已有项目策略优先。GitHub/上游页面会变化，实际配置前重新核对。文件中的来源支撑方法，不证明当前项目已有 CI、受保护分支或可靠部署。
