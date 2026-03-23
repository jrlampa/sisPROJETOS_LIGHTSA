#!/usr/bin/env sh
set -eu

current_branch="$(git rev-parse --abbrev-ref HEAD)"

if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
  echo "[verify_commit] Commit bloqueado: commits diretos em '$current_branch' nao sao permitidos."
  echo "[verify_commit] Use branch dev, feature/*, hotfix/* ou equivalente."
  exit 1
fi

staged_files="$(git diff --cached --name-only --diff-filter=ACMR)"

if [ -z "$staged_files" ]; then
  exit 0
fi

for file in $staged_files; do
  case "$file" in
    *.json|*.lock|*.toml|*.config.js|*/migrations/*|migrations/*|*/alembic/*|alembic/*)
      continue
      ;;
  esac

  if [ ! -f "$file" ]; then
    continue
  fi

  line_count="$(wc -l < "$file" | tr -d ' ')"

  if [ "$line_count" -gt 500 ]; then
    echo "[verify_commit] Commit bloqueado: arquivo '$file' com $line_count linhas (> 500)."
    echo "[verify_commit] Modularize o codigo antes de commitar."
    exit 1
  fi
done

exit 0
