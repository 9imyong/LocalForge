#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
set -a
source "$ROOT/.env.example"
if [[ -f "$ROOT/.env" ]]; then source "$ROOT/.env"; fi
set +a
[[ "$MODEL_DIR" = /* ]] || MODEL_DIR="$ROOT/$MODEL_DIR"
