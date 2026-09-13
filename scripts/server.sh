#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
case "${1:-}" in
up)
 [[ -f "$MODEL_DIR/$MODEL_FILE" ]] || { echo 'Run scripts/download.sh first'; exit 1; }
 template_mount=()
 template_args=()
 if [[ -n "${CHAT_TEMPLATE_FILE:-}" ]]; then
   template_path="$CHAT_TEMPLATE_FILE"
   [[ "$template_path" = /* ]] || template_path="$ROOT/$template_path"
   [[ -f "$template_path" ]] || { echo "Missing chat template: $template_path" >&2; exit 1; }
   template_mount=(--mount "type=bind,src=$template_path,dst=/config/chat-template.jinja,readonly")
   template_args=(--chat-template-file /config/chat-template.jinja)
 fi
 mkdir -p "$ROOT/.local/results"
 nvidia-smi -i "$GPU_ID" --query-gpu=memory.used,utilization.gpu --format=csv > "$ROOT/.local/results/gpu-before.csv"
 date +%s.%N > "$ROOT/.local/results/start-time"
 docker run --pull never -d --name localforge-baseline --gpus "device=$GPU_ID" --security-opt no-new-privileges --cap-drop ALL --read-only --tmpfs /tmp:rw,size=256m -p "127.0.0.1:$PORT:8080" -v "$MODEL_DIR:/models:ro" "${template_mount[@]}" "$IMAGE" --model "/models/$MODEL_FILE" --alias "$MODEL_ALIAS" --host 0.0.0.0 --port 8080 --ctx-size "$CONTEXT" --parallel 1 --n-gpu-layers "$GPU_LAYERS" --no-webui --offline --log-timestamps --log-verbosity "$LOG_VERBOSITY" --cors-origins localhost --jinja "${template_args[@]}"
 ;;
down) docker stop -t 30 localforge-baseline; docker rm localforge-baseline ;;
logs) docker logs --tail 100 localforge-baseline ;;
*) echo 'Usage: scripts/server.sh up|down|logs'; exit 2 ;;
esac
