---
id: ADR-001
status: 채택
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# ADR-001: llama.cpp CUDA baseline과 HTTP 경계

## 맥락

- 사용자가 llama.cpp를 최초 비교 기준 Runtime으로 지정
- WSL2 RTX 3090 확인, 호스트 nvcc·CMake 부재, Docker 사용 가능
- 호스트 시스템 패키지와 드라이버 변경 최소화 요구

## 결정

- 공식 llama.cpp 소스를 고정 commit에서 CUDA 12.8.1 Docker 빌드
- RTX 3090 대상 CUDA architecture 86, 빌드 병렬도 2
- 상위 클라이언트 경계는 HTTP Chat Completions와 SSE, 별도 Gateway·Agent 추상화 미도입
- baseline 모델: 공식 Qwen2.5-Coder-7B-Instruct GGUF Q4_K_M
- 선정 이유: 코딩 용도, 공식 단일 GGUF 배포, 약 4.68GB 가중치로 공유 24GB GPU에서 여유 확보 목적
- 모델의 한국어·실제 코딩 품질 우위 또는 최신 최고 모델이라는 판단은 제외
- 모델·Runtime revision과 파일 해시를 설정으로 관리
- 서비스는 호스트 127.0.0.1로만 게시, 모델은 읽기 전용 마운트

## 대안과 결과

| 대안 | 판단 |
|---|---|
| native CUDA 빌드 | host toolkit 설치가 필요해 이번 baseline에서는 보류 |
| 사전 빌드 서버 이미지 | 간단하지만 사용자 요청의 소스 CUDA 빌드 검증을 위해 미채택 |
| vLLM/SGLang | 후속 비교 대상, 최종 Runtime 선택 아님 |

- 내장 UI 빌드 및 사전 빌드 UI 다운로드 비활성화
- Docker 이미지·빌드 캐시 디스크 비용 발생
- GGUF 양자화와 다른 Runtime 정밀도가 다르면 성능 차이를 Runtime 단독 효과로 해석 불가
- 모델 라이선스 Apache-2.0, llama.cpp MIT; 재배포 시 해당 라이선스·고지 유지

## 근거

- [llama.cpp 공식 저장소 및 빌드 안내](https://github.com/ggml-org/llama.cpp)
- [공식 Qwen 모델 카드](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)
- 확인일: 2026-09-13, 실제 고정 revision은 저장소 `.env.example` 참조
