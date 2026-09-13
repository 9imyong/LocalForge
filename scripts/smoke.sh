#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
cd "$ROOT"
python3 scripts/smoke.py "$@"
