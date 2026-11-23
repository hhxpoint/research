#!/usr/bin/env bash
# hhxpoint/research installer for Linux / macOS.
# Usage: ./scripts/install.sh [--mode minimal|writing|full] [--only a,b] [--dsh-home PATH] [--dry-run]
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cli="$repo/tools/dsh_skills.py"
[ -f "$cli" ] || { echo "dsh_skills.py not found under $repo" >&2; exit 2; }

has_mode=0
for arg in "$@"; do
  case "$arg" in
    --mode|--mode=*) has_mode=1 ;;
  esac
done
if [ "$has_mode" -eq 0 ]; then
  set -- --mode full "$@"
fi

exec python3 "$cli" install "$@"
