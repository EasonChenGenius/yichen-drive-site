#!/bin/bash
# ============================================================
# 提交本次更新.command
# 双击运行：把当前所有改动存成一个版本，并推送到 GitHub 留痕。
#
# 安全说明：.gitignore 已排除 .env（高德 Key / 邮箱授权码）、
# __pycache__、3D 归档、临时选图页，这些不会被提交。
# ============================================================

cd "$(dirname "$0")" || exit 1

# 远程已配置为 git@github.com 的 SSH 方式，不需要、也不走 HTTP 代理。
# 若首次使用前还没把公钥加到 GitHub，推送会提示权限不足，按版本留痕说明.md 操作即可。

say()   { osascript -e "display dialog \"$1\" buttons {\"好\"} default button \"好\" with title \"YICHEN Drive 版本留痕\" with icon note" >/dev/null 2>&1; }
ask()   { osascript -e "text returned of (display dialog \"$1\" default answer \"$2\" buttons {\"取消\",\"继续\"} default button \"继续\" with title \"YICHEN Drive 版本留痕\")" 2>/dev/null; }

# 1. 检查改动
if [ -z "$(git status --porcelain)" ]; then
  say "没有检测到任何改动，无需提交。"
  exit 0
fi

echo "=============================================="
echo " 本次将要纳入版本的改动："
echo "=============================================="
git status --short
echo ""

# 2. 询问更新说明
MSG=$(ask "本次更新做了什么？
（会永久保存在版本历史里，请写清楚，例如：填写考斯特与 GL8 真实年款与座位）" "")

if [ -z "$MSG" ]; then
  say "未填写更新说明，已取消。"
  exit 1
fi

# 3. 提交
git add -A
if ! git commit -m "$MSG"; then
  say "提交失败，请到终端查看原因。"
  exit 1
fi

echo ""
echo "→ 已生成本地版本：$(git log --oneline -1)"

# 4. 推送到 GitHub
echo "→ 正在推送到 GitHub..."
if ! git push origin main; then
  say "推送失败（可能是网络问题）。
本地版本已保存，恢复网络后在终端执行：git push origin main"
  exit 1
fi

# 5. 可选：打版本标签
TAG=$(ask "要给这个版本打标签吗？
（重要节点建议打，例如 v50 / 上线-20261101；留空表示不打）" "")

if [ -n "$TAG" ]; then
  git tag -a "$TAG" -m "$MSG" && git push origin "$TAG" && echo "→ 标签 $TAG 已推送"
fi

echo ""
echo "=============================================="
echo " 完成。当前最新版本："
git log --oneline -3
echo "=============================================="

say "已保存到 GitHub：
$(git log --oneline -1)

查看完整历史：https://github.com/EasonChenGenius/yichen-drive-site/commits/main"

open "https://github.com/EasonChenGenius/yichen-drive-site/commits/main" 2>/dev/null
