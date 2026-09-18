---
name: rick-skill-pub
description: 把指定的 Agent Skill 通过严格安全门禁检查后发布到 GitHub 公共仓库 li2810081/rick_skills，并维护仓库 README 技能索引。用于用户说“发布 Skill 到 GitHub”“发布到技能仓”“收录到我的技能库”“更新 rick_skills 里的技能”“同步技能到 GitHub”。不用于修改 Skill 内容、创建新 Skill、发布到钉钉知识库（那是 yundu-skill-pub），也不用于发布非技能类文件。
---

# rick-skill-pub — 发布技能到 GitHub 技能仓

把指定 Skill 发布到 GitHub 公共仓库 `li2810081/rick_skills`。安全门禁是硬约束：任何疑似 API 密钥、令牌、私钥、凭证，一票否决，不发布。

## 固定信息

- 仓库：`li2810081/rick_skills`（公开），分支 `main`，技能放 `skills/<skill-name>/`，一个技能一个目录。
- 本地克隆固定在 `D:/AI/rick_skills`；不存在时先 `gh repo clone li2810081/rick_skills D:/AI/rick_skills`。
- 认证只用本机已登录的 `gh` CLI。禁止创建、导出、回显任何 token；禁止把凭据写进 remote URL 或任何配置文件。
- 门禁扫描脚本：本技能目录下的 `rick-gate.sh`，用法 `bash rick-gate.sh <目标目录>`，退出码 0=PASS、1=BLOCK。
- 每次发布必须同步维护仓库 README 的「技能索引」表。

## 1. 确定发布对象

1. 用户点名了技能名或路径就用它；只说“发布这个技能”时，取当前上下文唯一确定的技能目录。
2. 查找顺序：用户给的路径 → `C:/Users/root/.agents/skills/<name>` → `C:/Users/root/.zcode/skills/<name>`。
3. 无法唯一确定时停下询问，不要猜。
4. 重新读取源目录清单和 `SKILL.md`，不沿用缓存：目录名必须等于 `SKILL.md` 的 `name`（仅小写字母、数字、连字符），`description` 非空。

## 2. 安全门禁（硬性，一票否决）

对源目录执行门禁扫描，三道检查：文件名黑名单（.env、私钥/证书文件、`*credential*`、`*secret*`、`*password*`、`.npmrc`、各类凭证 JSON）、已知令牌正则（GitHub/AWS/Google/OpenAI/Slack/GitLab/Shopify/npm/私钥块等）、硬编码赋值扫描（api_key/secret/token/password 等关键词后跟引号字符串）。

- BLOCK：停止发布。只报告「相对路径 + 行号 + 风险类型」，绝不展示、复述或引用匹配内容本身。等用户脱敏后重新扫描，PASS 才能继续。
- 明显占位符（your、`<...>`、`${VAR}`、xxx、示例值等）放行，但必须在结果中列出清单。
- 含图片或二进制文件时：提示用户人工确认无密钥截图，未确认不得发布。

## 3. 同步进仓库

```bash
cd D:/AI/rick_skills && git pull --rebase
rm -rf skills/<name> && cp -r <源目录> skills/<name>
find skills/<name> \( -name '__pycache__' -o -name 'node_modules' -o -name '.git' -o -name '*.zip' -o -name '*.log' -o -name '.DS_Store' -o -name 'Thumbs.db' \) -exec rm -rf {} +
```

- 整目录替换是标准行为，历史版本由 git 历史保留，无需逐次确认。
- 替换后对 `skills/<name>` 重跑门禁扫描，必须 PASS。
- `git add -A skills/<name>`，然后比较暂存文件数与源目录文件数（扣除已清理的杂物）：不一致说明有文件被 .gitignore 拦下，这属于安全拦截，按 BLOCKED 报告并说明文件名，不得绕过。
- 更新 README「技能索引」：已有该技能行 → 只更新需要变更的列；没有 → 按现有表格格式追加一行；然后 `git add README.md`。

## 4. 提交与推送

- 提交信息：`publish(<name>): <一句话变更>`。
- `git push origin main`。
- 被 GitHub Push Protection 拦截时：如实报告「GitHub 拦截」，绝不绕过（不加 `--force`、不跳过扫描）；先脱敏，重扫 PASS 后再推。

## 5. 远端验收（缺一不可）

```bash
git -C D:/AI/rick_skills rev-parse HEAD
git -C D:/AI/rick_skills ls-remote origin refs/heads/main   # 必须等于本地 HEAD
gh api repos/li2810081/rick_skills/contents/skills/<name> --jq '.[].name'
gh api repos/li2810081/rick_skills/contents/README.md --jq '.content' | base64 -d   # 确认索引行已在线
```

## 6. 完成证据

发布完成必须同时给出：① 源目录路径与文件数；② 门禁扫描 RESULT: PASS（含占位符清单）；③ 提交 SHA 且远端 main 一致；④ 远端 `skills/<name>/` 文件清单与 README 索引回读。缺任一按 BLOCKED 报告，不得说“发布完成”。

## 错误处理

- push 因网络/SSH 连接中断失败（如 “Connection closed by UNKNOWN port”）：不改配置，原样重试一次；仍失败按 BLOCKED 报告。
- pull 冲突或克隆损坏：BLOCKED，保留现场报告，不要自行 `reset --hard`。
- 禁止 force push、改写历史、操作他人仓库。
- `gh` 未登录：报告 BLOCKED，让用户先 `gh auth login`，不要代做。
