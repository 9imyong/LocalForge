#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
SRC="$ROOT/.local/runtime/llama.cpp"
mkdir -p "$(dirname "$SRC")"
if [[ ! -d "$SRC/.git" ]]; then git clone https://github.com/ggml-org/llama.cpp.git "$SRC"; fi
if ! git -C "$SRC" cat-file -e "$LLAMA_REV^{commit}"; then git -C "$SRC" fetch origin "$LLAMA_REV"; fi
[[ -z "$(git -C "$SRC" status --porcelain)" ]] || { echo 'Runtime source has local changes'; exit 1; }
git -C "$SRC" checkout --detach "$LLAMA_REV"
docker build -f "$ROOT/docker/Dockerfile" -t "$IMAGE" "$SRC"
