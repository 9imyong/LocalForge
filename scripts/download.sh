#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$MODEL_DIR"
FILE="$MODEL_DIR/$MODEL_FILE"
verify() { printf '%s  %s\n' "$MODEL_SHA256" "$1" | sha256sum --check --status; }
if [[ -f "$FILE" ]]; then verify "$FILE"; exit; fi
curl --fail --location --retry 3 --continue-at - "https://huggingface.co/$MODEL_REPO/resolve/$MODEL_REV/$MODEL_FILE" -o "$FILE.part"
verify "$FILE.part" || { echo 'Model SHA256 mismatch'; exit 1; }
mv "$FILE.part" "$FILE"
