#!/usr/bin/env bash
# Install the agy-cli skill for Claude Code (manual alternative to the plugin marketplace).
#   ./install.sh           copy skills/agy-cli to ~/.claude/skills/agy-cli
#   ./install.sh --link    symlink instead, so edits in this repo take effect immediately
#   ./install.sh --force   replace an existing installed copy
# The target folder can be changed with CLAUDE_SKILLS_DIR (default ~/.claude/skills).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$repo/skills/agy-cli"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/agy-cli"
link=0
force=0

for arg in "$@"; do
  case "$arg" in
    --link) link=1 ;;
    --force) force=1 ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

if [ -L "$dest" ]; then
  rm "$dest"
elif [ -e "$dest" ]; then
  if [ "$force" != 1 ]; then
    echo "$dest already exists; re-run with --force to replace it" >&2
    exit 1
  fi
  rm -rf "$dest"
fi

mkdir -p "$(dirname "$dest")"
if [ "$link" = 1 ]; then
  ln -s "$src" "$dest"
else
  cp -R "$src" "$dest"
  find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
fi
echo "installed: $dest"

if ! command -v agy >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/agy" ]; then
  echo "warning: agy not found; install the Antigravity CLI and sign in before generating images" >&2
fi

python3 "$dest/scripts/agy_image.py" setup
