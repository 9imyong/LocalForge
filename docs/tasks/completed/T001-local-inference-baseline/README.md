---
id: T001-local-inference-baseline
status: Done
owner: LocalForge
created: 2026-09-13
updated: 2026-09-13
---

# T001: Local Inference Baseline

## 목표와 범위

- [요구사항](../../../requirements/REQ-INFERENCE-001.md)의 로컬 CUDA 추론·API·기초 측정 범위 구현
- 사용자 지정 경로에서 진행 기록 관리 후 완료되어 `docs/tasks/completed/`로 이동
- Agent 연동(요구사항 05·14), 외부 클라이언트(09), 다른 Runtime 비교는 이번 작업 제외

## 계획 및 진행

- [x] 저장소 규칙·요구사항 확인
- [x] WSL2·RTX 3090 확인: 24,576 MiB, 드라이버 591.86
- [x] 호스트 변경 없이 Docker CUDA 빌드 방식 선택
- [x] 모델 revision·SHA256 고정 및 다운로드 도구 작성
- [x] 실행·종료·로그·스모크·측정 도구 작성
- [x] 스트리밍 파서 단위 테스트 4개 통과, shell 구문 검사 통과
- [x] CUDA 빌드 완료
- [x] 모델 SHA256 검증 완료
- [x] 실제 CUDA offload·모델 로드 확인
- [x] 일반·스트리밍 API 통합 테스트 통과
- [x] TTFT·throughput·GPU 메모리 측정
- [x] 재기동 후 재검증
- [x] 결과·위험 기록 후 완료 이동

## 검증 기록

- sandbox 내부 NVML 접근 실패, 허용된 외부 점검에서 정상 GPU 인식
- 빌드 시작 전 GPU 전체 메모리 사용량 약 6,162 MiB; 기존 프로세스 변경 없음
- `.local/build.log`, `.local/download.log`, `.local/results/`에 로컬 실행 증거 저장
- `make preflight` 실제 명령 통과: GPU·Docker·도구·저장 공간 확인
- 기존 Git 추적의 `.local` Runtime gitlink·다운로드 메타데이터 2건은 실파일 보존 후 index에서 제거; 모델 가중치 추적 없음
- 공식 GGUF 4,683,073,536 bytes 다운로드 및 SHA256 일치 확인
- 변경 문서 6개 markdownlint 오류 0건, 상대 링크 검사 통과
- 최초 CUDA 컴파일 완료 후 실행파일 링크에서 드라이버 심볼 해석 실패; 공식 Docker 빌드와 동일한 allow-shlib-undefined 옵션 추가 후 재빌드
- 후속 재빌드용 CMake 빌드 캐시 추가
- 일반·스트리밍 API와 GPU 증거 수집 통과, 종료·재기동 후 재검증 통과
- GPU 29/29 레이어 offload, 모델 초기화 4.066초, warm TTFT 12.868~21.604ms, 생성 속도 88.451~92.327 tokens/s
- 수동 한국어·코딩 응답 확인, 일부 중국어 단어 혼입으로 품질 평가 후속 필요
- 상세 측정 조건과 한계: [검증 결과](../../../operations/baseline-results.md)

## 관련 문서

- [구조](../../../architecture/localforge-runtime.md)
- [결정](../../../decisions/ADR-001-inference-runtime-baseline.md)
- [API](../../../specs/inference-api.md)
- [실행 절차](../../../../README.md)

## 위험 및 복구

- 다른 GPU 작업이 동시에 실행 중이므로 전체 장치 VRAM·utilization은 본 서비스 전용 수치가 아님
- 최초 이미지·모델 다운로드 시간과 CUDA 빌드 시간 필요
- `make down`으로 전용 컨테이너 종료·제거; 모델·소스·결과는 `.local/`에 유지
- 다른 서비스, Windows 드라이버, 호스트 CUDA 설정 변경 금지
- 완료 조건 미충족 시 Done 표시 또는 completed 이동 금지
