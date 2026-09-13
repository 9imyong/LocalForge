#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
mkdir -p "$ROOT/.local/results"
docker logs localforge-baseline > "$ROOT/.local/results/server.log" 2>&1
docker image inspect "$IMAGE" --format '{{.Id}}' > "$ROOT/.local/results/image-id.txt"
nvidia-smi -i "$GPU_ID" --query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version --format=csv > "$ROOT/.local/results/gpu.csv"
python3 - "$ROOT/.local/results/server.log" <<'PY'
import json, re, sys
from pathlib import Path
s=Path(sys.argv[1]).read_text()
lines=[line for line in s.splitlines() if re.search(r'CUDA[0-9]|offloaded .* layers|load time|model loaded', line)]
for line in lines:
 print(line)
def stamp(line):
 m=re.search(r'(\d+)\.(\d{2})\.(\d{3})\.(\d{3})', line)
 return (int(m[1])*60+int(m[2])+int(m[3])/1000+int(m[4])/1000000) if m else None
starts=[stamp(x) for x in s.splitlines() if "loading model '" in x]
ends=[stamp(x) for x in s.splitlines() if 'model loaded' in x]
load_time=ends[-1]-starts[0] if starts and ends and starts[0] is not None and ends[-1] is not None else None
Path(sys.argv[1]).with_name('load-time.json').write_text(json.dumps({'model_initialization_seconds': load_time, 'definition': 'loading model to model loaded, includes context and warmup'})+'\n')
print('model_initialization_seconds:', load_time)
if not re.search(r'offloaded [1-9][0-9]*/[0-9]+ layers to GPU',s):
 raise SystemExit('GPU offload evidence not found: inspect full local server log')
PY
