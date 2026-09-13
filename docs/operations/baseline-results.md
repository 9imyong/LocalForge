---
status: 현재
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# llama.cpp baseline 검증 결과

## 실행 조건

- WSL2 Ubuntu, RTX 3090 24,576 MiB, NVIDIA driver 591.86
- llama.cpp commit `56b9eb280a67796379d8625729fb03d72c70789d`
- CUDA 12.8.1 이미지에서 소스 빌드, CUDA compiler 12.8.93, architecture 86
- Qwen2.5-Coder-7B-Instruct GGUF Q4_K_M, 모델 revision·해시는 `.env.example` 참조
- context 4,096, parallel 1, temperature 0, 최대 출력 128토큰
- 동일 한국어 Python 질문, 일반 응답 1회 워밍업 후 스트리밍 3회
- 결과는 짧은 동일 프롬프트의 warm/cache baseline, 일반 작업 전체 성능 대표값 아님

## 통과한 검증

- WSL2 GPU 인식, CUDA 소스 빌드, GGUF SHA256 검증
- `/health`, `/v1/models`, 일반 Chat Completions, 스트리밍 content·finish_reason·DONE·usage 확인
- 종료·제거 후 동일 명령으로 재기동, 일반 응답·스트리밍 재검증
- GPU offload 29/29 레이어, CUDA0 모델·KV·compute 버퍼 확인
- 파서 단위 테스트 4개, shell 구문 검사, 문서 Markdown·링크 검사
- 수동 코드 응답에서 올바른 `add(a, b)` 함수 확인; 생성 코드 실행은 수행하지 않음

## 재기동 후 측정

| 지표 | 결과 | 해석 |
| --- | --- | --- |
| 모델 초기화 | 4.066초 | loading model → model loaded, context·warmup 포함 |
| 시작 → 준비 확인 | 6.451초 | Docker 시작·polling 포함 |
| TTFT | 21.604 / 13.390 / 12.868ms | 첫 내용 청크까지, prompt cache 57토큰 재사용 |
| 서버 생성 속도 | 92.327 / 91.999 / 88.451 tokens/s | 서버 timings.predicted_per_second |
| 요청 전체 시간 | 1.397 / 1.394 / 1.449초 | 각 128토큰 출력 |
| CUDA 모델 버퍼 | 4,168.09 MiB | 모델용 할당 |
| CUDA KV 버퍼 | 224.00 MiB | context 4K |
| CUDA compute 버퍼 | 136.01 MiB | 계산 버퍼 |
| 장치 전체 peak VRAM | 7,822 MiB | 다른 GPU 프로세스 포함 가능 |
| 장치 전체 peak utilization | 97% | 약 0.2초 간격 샘플, 서비스 전용 수치 아님 |

- 첫 실행 모델 초기화: 14.968초; 재기동과 파일 캐시 조건이 달라 직접 성능 개선으로 해석 금지
- 첫 실행 스트리밍: TTFT 14.862~29.040ms, 서버 생성 속도 89.437~90.564 tokens/s
- 전용 GPU 할당과 장치 전체 VRAM 구분 필수

## 남은 위험과 다음 단계

- 짧은 3회 측정이며 부하·장시간 안정성·실제 Coding Agent 품질 검증 아님
- 수동 한국어 설명에 중국어 단어 혼입 관찰: 한국어 품질 합격을 주장하지 않음
- 비교 모델 및 한국어·코딩 평가 세트는 후속 작업
- Runtime 간 비교 시 모델·정밀도·tokenizer·context·cache 조건 통제 필요
- Agent 도구 호출, MacBook·LAN 접근, 인증 확장은 이번 단계 제외
- 처음 링크 실패는 공식 CUDA Dockerfile의 allow-shlib-undefined 옵션 적용으로 해결
- 최초 빌드는 큰 이미지 다운로드와 CUDA 컴파일 필요, 후속 CMake 캐시 재사용
- 실행 컨테이너는 localhost:18000에 유지, `make down`으로 종료 가능

## 증거 위치

- `.local/build.log`: 최종 CUDA 빌드 로그
- `.local/results/smoke-first.json`: 첫 기동 API·성능 결과
- `.local/results/smoke.json`: 재기동 결과
- `.local/results/server.log`: GPU offload 및 모델 초기화 로그
- `.local/results/load-time.json`: 모델 초기화 시간
- `.local/results/gpu-before.csv`, `gpu.csv`, `image-id.txt`: 장치·이미지 식별 결과
- 결과 파일은 개인 환경 산출물로 Git 제외, 공유용 수치만 본 문서에 기록

## Tool Calling 후속 변경

- 본문의 T001 성능 결과는 당시 내장 template의 측정 기록으로 보존
- 동일 가중치·Runtime·context에서 도구 호환 template 및 OpenCode fixture 검증 추가
- 현재 구성·회귀 결과: [Tool Calling 운영 기록](tool-calling.md)
