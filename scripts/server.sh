#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
case "${1:-}" in
up)
 [[ -f "$MODEL_DIR/$MODEL_FILE" ]] || { echo 'Run scripts/download.sh first'; exit 1; }
 mkdir -p "$ROOT/.local/results"
 date +%s.%N > "$ROOT/.local/results/start-time"
 docker run -d --name localforge-baseline --gpus "device=$GPU_ID" --security-opt no-new-privileges --cap-drop ALL --read-only --tmpfs /tmp:rw,size=256m -p "127.0.0.1:$PORT:8080" -v "$MODEL_DIR:/models:ro" "$IMAGE" --model "/models/$MODEL_FILE" --alias "$MODEL_ALIAS" --host 0.0.0.0 --port 8080 --ctx-size "$CONTEXT" --parallel 1 --n-gpu-layers "$GPU_LAYERS" --no-webui
 ;;
down) docker stop -t 30 localforge-baseline; docker rm localforge-baseline ;;
logs) docker logs --tail 100 localforge-baseline ;;
*) echo 'Usage: scripts/server.sh up|down|logs'; exit 2 ;;
esac
