#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$ROOT/.local/tools/opencode"
cp "$ROOT/configs/opencode/"package*.json "$ROOT/.local/tools/opencode/"
npm ci --prefix "$ROOT/.local/tools/opencode"
"$ROOT/.local/tools/opencode/node_modules/.bin/opencode" --version
docker build -t localforge/opencode-sandbox:1.18.30 "$ROOT/configs/opencode"
