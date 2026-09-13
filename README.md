# LocalForge

WSL2의 개인 GPU에서 실행하는 로컬 LLM API와 Runtime 비교 기준 환경.

- 초기 Runtime: llama.cpp CUDA, 최종 Runtime 확정 아님
- 장비: Windows 11 / WSL2 Ubuntu / RTX 3090 24GB
- 모델: Qwen2.5-Coder-7B-Instruct GGUF Q4_K_M, 모델 revision·SHA256 고정
- 범위: 로컬 API, 스트리밍, 기초 성능 측정; Agent·외부 클라이언트 연결은 후속

## 실행

전제: WSL2에서 NVIDIA GPU 접근 가능, Docker GPU 지원, git·curl·Python 3·make·sha256sum 사용 가능. 호스트 CUDA toolkit 설치 불필요. 최초 수 GB 이미지·모델 다운로드 및 CUDA 소스 빌드 필요.

```bash
cp .env.example .env
make preflight
make build
make model
make up
make smoke
make evidence
make logs
make down
```

- 기본 LOG_VERBOSITY=4: CUDA offload 진단 포함, 개인 프롬프트 사용 시 debug 5 이상 설정 주의
- `.env`는 신뢰하는 로컬 shell 설정 파일, Git 제외
- `MODEL_DIR`, `MODEL_FILE`, `MODEL_SHA256`, `MODEL_REV`, `MODEL_REPO`를 모델 변경 시 함께 지정
- Runtime 변경 시 `LLAMA_REV`와 `IMAGE`를 함께 갱신하고 재빌드
- 포트 기본 18000, 호스트 `127.0.0.1`에만 게시
- `make up`은 컨테이너 시작만 수행, 준비·추론 성공은 `make smoke`로 확인
- `make down` 후 `make up`으로 재실행, 중복 up은 기존 컨테이너가 있으면 실패
- 타 서비스 종료·드라이버 교체·시스템 CUDA 변경 없음

## API 예제

```bash
curl http://127.0.0.1:18000/v1/models
curl http://127.0.0.1:18000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"localforge-baseline","messages":[{"role":"user","content":"파이썬 리스트를 설명해줘"}],"max_tokens":128,"stream":false}'
```

## 검증과 측정

```bash
make test
bash scripts/smoke.sh --runs 5
nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv
```

- 결과: `.local/results/smoke.json`, 일반 응답 1건 워밍업 후 스트리밍 3건 기본 측정
- TTFT: 요청 전송 직전부터 첫 비어 있지 않은 content 청크까지
- 생성 속도 추정: `(completion_tokens - 1) / (마지막 content 시각 - 첫 content 시각)`
- `server_timings_optional`: llama.cpp가 제공하는 선택적 서버 측 timing 원문, predicted_per_second가 서버 decode throughput
- 청크 단위 측정이므로 정확한 서버 decode throughput과 구분; 전체 요청 tokens/s도 별도 기록
- GPU 값: 0.2초 주기 장치 전체 샘플, 다른 프로세스 점유 포함, 순간 peak 누락 가능
- `make evidence`의 `load-time.json`: 서버 loading model부터 model loaded까지, context 초기화·warmup 포함 모델 초기화 시간
- start-to-ready: 최근 up의 시작 시각부터 health 200 관찰까지; 실제 model load 시간은 서버 로그의 load time과 별도 확인
- 재기동 직후 즉시 smoke 실행 권장, 늦게 실행한 경우 start-to-ready에 대기 시간이 포함됨
- 반복 동일 프롬프트의 캐시 영향 존재, Runtime 간 본격 비교 수치로 사용하지 않음
- CUDA 증거: `make logs`에서 CUDA 장치·GPU offload 레이어 확인, VRAM 증가만으로 GPU 추론 판정 금지

## 문제 확인

- GPU 접근 실패: WSL2 외부 터미널에서도 nvidia-smi 확인; 시스템 드라이버 자동 변경 금지
- OOM: 다른 GPU 작업 점유 확인 후 context·GPU layer 설정 조정, CPU offload가 발생하면 결과에 명시
- 모델 손상: download 스크립트 SHA256 검사 실패 시 파일을 조사하고 재다운로드
- 포트 충돌: `.env`의 PORT 수정 후 재실행
- 모델 교체: `make down` → 모델 관련 설정 변경 → `make model` → `make up` → `make smoke`

## 문서

- [요구사항](docs/requirements/REQ-INFERENCE-001.md)
- [아키텍처](docs/architecture/localforge-runtime.md)
- [baseline 결정](docs/decisions/ADR-001-inference-runtime-baseline.md)
- [API 부분집합](docs/specs/inference-api.md)
- [실측 결과와 남은 위험](docs/operations/baseline-results.md)
- [작업 기록](tasks/T001-local-inference-baseline/README.md)
- [작업 규칙](AGENTS.md), [커밋 규칙](COMMIT_RULES.md)

모델·Runtime의 라이선스는 각 공식 배포의 조건 적용. LocalForge 자체 라이선스는 미선정.
