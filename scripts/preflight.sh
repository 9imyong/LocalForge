#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
uname -r
nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv
docker version --format '{{.Server.Version}}'
for tool in git curl sha256sum python3; do command -v "$tool"; done
df -h "$ROOT"
