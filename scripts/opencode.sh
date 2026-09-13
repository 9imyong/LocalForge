#!/usr/bin/env bash
# Linux/WSL2: isolated client container, localhost inference endpoint.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
workspace=${1:?Usage: bash scripts/opencode.sh WORKSPACE [opencode arguments...]}
shift
workspace=$(realpath "$workspace")
[[ -d "$workspace/.git" ]] || { echo 'A dedicated Git workspace is required' >&2; exit 1; }
state="$ROOT/.local/opencode-container-state"
mkdir -p "$state"
terminal=()
if [[ -t 0 && -t 1 ]]; then terminal=(-it); fi
config=${LOCALFORGE_OPENCODE_CONFIG:-$ROOT/configs/opencode/opencode.json}
config=$(realpath "$config")
exec docker run "${terminal[@]}" --rm --init --name "${LOCALFORGE_OPENCODE_CONTAINER:-localforge-opencode-$$}" --network host --user "$(id -u):$(id -g)" \
  --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,exec,size=256m \
  -e OPENCODE_CONFIG=/config/opencode.json \
  -e "LOCALFORGE_BASE_URL=${LOCALFORGE_BASE_URL:-http://127.0.0.1:18000/v1}" \
  -e OPENCODE_DISABLE_AUTOUPDATE=true -e OPENCODE_DISABLE_MODELS_FETCH=true \
  --mount "type=bind,src=$ROOT/.local/tools/opencode/node_modules/opencode-linux-x64/bin/opencode,dst=/tools/opencode,readonly" \
  --mount "type=bind,src=$config,dst=/config/opencode.json,readonly" \
  --mount "type=bind,src=$workspace,dst=/workspace" \
  --mount "type=bind,src=$state,dst=/state" \
  localforge/opencode-sandbox:1.18.30 "$@"
