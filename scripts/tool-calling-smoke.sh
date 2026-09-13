#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
python3 "$ROOT/scripts/tool-calling-smoke.py" --base-url "http://127.0.0.1:$PORT/v1" --model "$MODEL_ALIAS" "$@"
