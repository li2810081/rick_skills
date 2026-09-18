#!/usr/bin/env bash
# rick-skill-pub 安全门禁扫描
# 用法: bash rick-gate.sh <skill目录>   退出码: 0=PASS, 1=BLOCK
# 规则: 只输出「文件:行号 + 风险类型」，绝不输出匹配到的内容本身。
set -u
SRC="$1"; fail=0
EXC=(--exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=node_modules)

echo "== [1/3] 文件名黑名单 =="
files=$(find "$SRC" -type f \( \
  -name '.env' -o -name '.env.*' -o -name '*.pem' -o -name '*.key' -o \
  -name '*.pfx' -o -name '*.p12' -o -name '*.jks' -o -name '*.keystore' -o \
  -name 'id_rsa*' -o -name 'id_ecdsa*' -o -name 'id_ed25519*' -o \
  -name '*credential*' -o -name '*password*' -o -name '*secret*' -o \
  -name '*.token' -o -name 'auth.json' -o -name '.npmrc' -o -name '.netrc' -o \
  -name '.git-credentials' -o -name 'client_secret*.json' -o -name 'service-account*.json' \
  \) | sed "s|^$SRC/||")
if [ -n "$files" ]; then
  echo "BLOCK: 命中黑名单文件名（禁止发布）:"; echo "$files"; fail=1
else echo "通过"; fi

echo "== [2/3] 已知令牌正则 =="
tok=$(grep -rnIE \
  'gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk-(proj-)?[A-Za-z0-9_-]{20,}|xox[abposr]-[A-Za-z0-9-]{10,}|glpat-[A-Za-z0-9_-]{20,}|dop_v1_[a-f0-9]{64}|shpat_[A-Za-z0-9]{32}|npm_[A-Za-z0-9]{36}|BEGIN [A-Z ]*PRIVATE KEY' \
  "${EXC[@]}" "$SRC" | sed "s|^$SRC/||; s|^\([^:]*:[0-9]*\):.*|\1|" || true)
if [ -n "$tok" ]; then
  echo "BLOCK: 已知令牌格式（禁止发布）:"; echo "$tok"; fail=1
else echo "通过"; fi

echo "== [3/3] 硬编码赋值扫描 =="
sus=$(grep -rniE \
  "(api[_-]?key|apikey|secret|token|password|passwd|pwd|credential)[[:space:]]*[:=][[:space:]]*[\"'][^\"']{12,}[\"']" \
  "${EXC[@]}" "$SRC" | sed "s|^$SRC/||; s|^\([^:]*:[0-9]*\):.*|\1|" || true)
PH='(your|<[^>]*>|\$\{?[A-Za-z_]|xxx|\.\.\.|replace[_-]?me|example|dummy|placeholder|change[_-]?me|\*\*)'
real=$(printf '%s\n' "$sus" | grep -viE "$PH" || true)
phits=$(printf '%s\n' "$sus" | grep -iE "$PH" || true)
if [ -n "$real" ]; then
  echo "BLOCK: 疑似硬编码密钥（禁止发布）:"; echo "$real"; fail=1
else echo "通过"; fi
if [ -n "$phits" ]; then echo "ALLOWED-PLACEHOLDER（占位符放行，需列入清单）:"; echo "$phits"; fi

if [ "$fail" -eq 1 ]; then echo "RESULT: BLOCK"; exit 1; fi
echo "RESULT: PASS"
