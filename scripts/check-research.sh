#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
files=(
  README.md
  docs/hypotheses.md
  docs/experiment-protocol.md
  docs/source-audit.md
  docs/operator-validation.md
  docs/experiment-readiness.md
  docs/decisions/0001-validation-before-implementation.md
  docs/findings/0001-admission-vs-apf.md
)
for file in "${files[@]}"; do
  if [[ ! -s "$file" ]]; then
    printf 'Missing or empty: %s\n' "$file" >&2
    exit 1
  fi
done
printf 'Research document presence check passed (%s files).\n' "${#files[@]}"
