---
id: REQ-INFERENCE-001
title: LocalForge 로컬 LLM 추론 환경 구축
status: 초안
owners: [LocalForge]
created: 2026-09-13
last_reviewed: 2026-09-13
---

# 요구사항: LocalForge 로컬 LLM 추론 환경 구축

## 목적과 문제

현재 개발 작업에서 사용하는 LLM은 외부 AI 서비스 및 특정 클라이언트에 의존하고 있으며, 개인 GPU 자원을 활용한 로컬 추론 환경과 AI Coding Agent 실행 환경이 구축되어 있지 않다.

LocalForge는 개인 개발 환경에서 로컬 LLM을 실행하고 OpenAI-compatible API를 통해 AI Agent 및 개발 도구가 모델을 사용할 수 있는 공통 추론 환경을 제공하는 것을 목표로 한다.

초기 환경은 Windows PC의 WSL2와 NVIDIA RTX 3090 24GB를 기준으로 구축한다.

향후 MacBook 등 다른 클라이언트에서도 동일한 API를 통해 LocalForge를 사용할 수 있어야 하며, 특정 LLM Runtime에 강하게 종속되지 않는 구조를 지향한다.

초기 Runtime은 llama.cpp를 baseline으로 사용하되, 향후 SGLang, vLLM 및 기타 Runtime을 비교·교체할 수 있어야 한다.

## 이해관계자

| 역할             | 필요한 결과                                                  |
| -------------- | ------------------------------------------------------- |
| 개발자            | 로컬 LLM을 Coding Agent 및 개발 도구에서 사용할 수 있어야 한다.            |
| LocalForge 운영자 | 모델, Runtime, 설정 및 GPU 자원 사용 상태를 관리할 수 있어야 한다.           |
| AI Agent       | 표준화된 API를 통해 LLM 추론 기능을 사용할 수 있어야 한다.                   |
| 외부 클라이언트       | 향후 MacBook 등 다른 장치에서도 동일한 LocalForge API에 접근할 수 있어야 한다. |

## 요구사항

* REQ-INFERENCE-001-01: LocalForge는 RTX 3090 GPU를 이용하여 로컬 LLM 추론을 수행할 수 있어야 한다.
* REQ-INFERENCE-001-02: 초기 추론 Runtime으로 llama.cpp를 지원해야 한다.
* REQ-INFERENCE-001-03: Runtime은 특정 구현에 강하게 결합되지 않아야 하며 향후 SGLang, vLLM 등의 Runtime을 추가할 수 있어야 한다.
* REQ-INFERENCE-001-04: 추론 서비스는 OpenAI-compatible API를 제공해야 한다.
* REQ-INFERENCE-001-05: OpenCode, Aider 등 외부 AI Coding Agent가 LocalForge API를 사용할 수 있어야 한다.
* REQ-INFERENCE-001-06: 모델과 Runtime 설정은 코드 변경 없이 구성값을 통해 변경할 수 있어야 한다.
* REQ-INFERENCE-001-07: 모델 파일, Runtime, Agent 및 프로젝트 코드는 서로 독립적으로 관리할 수 있어야 한다.
* REQ-INFERENCE-001-08: 초기 환경은 Windows 11 + WSL2 Ubuntu + NVIDIA RTX 3090 24GB에서 동작해야 한다.
* REQ-INFERENCE-001-09: 향후 동일 네트워크 또는 안전한 사설 네트워크를 통해 MacBook 등 다른 클라이언트가 LocalForge API를 사용할 수 있어야 한다.
* REQ-INFERENCE-001-10: LLM API가 인터넷에 인증 없이 직접 노출되어서는 안 된다.
* REQ-INFERENCE-001-11: 동일한 모델과 조건에서 Runtime별 추론 성능을 비교할 수 있는 Benchmark 절차를 제공해야 한다.
* REQ-INFERENCE-001-12: Benchmark는 최소 TTFT, generation throughput, VRAM 사용량, model load time을 측정할 수 있어야 한다.
* REQ-INFERENCE-001-13: LocalForge의 Runtime 변경이 Agent 사용 방식에 불필요한 변경을 발생시키지 않아야 한다.
* REQ-INFERENCE-001-14: Agent가 프로젝트 파일 탐색, 수정, 명령 실행 및 테스트 수행에 LLM을 사용할 수 있어야 한다.

## 인수 조건

```text
주어진 조건:
- Windows 11
- WSL2 Ubuntu
- NVIDIA RTX 3090 24GB
- 지원되는 로컬 LLM 모델이 준비되어 있다.

실행할 때:
- LocalForge inference service를 실행한다.
- OpenAI-compatible API를 통해 chat completion 요청을 전송한다.

기대 결과:
- GPU를 사용하여 모델 추론이 수행된다.
- API가 정상적인 응답 또는 streaming response를 반환한다.
- 요청 및 응답 과정에서 치명적인 Runtime 오류가 발생하지 않는다.
```

```text
주어진 조건:
- LocalForge inference service가 실행 중이다.
- Coding Agent가 설치되어 있다.

실행할 때:
- Agent가 LocalForge API를 모델 Provider로 사용한다.
- Agent에게 저장소 분석 및 코드 관련 작업을 요청한다.

기대 결과:
- Agent가 LocalForge LLM과 정상적으로 통신한다.
- 프로젝트 파일을 읽고 모델의 판단에 따라 필요한 도구를 호출할 수 있다.
- 수행 결과와 검증 결과를 사용자에게 보고한다.
```

```text
주어진 조건:
- 동일 모델과 동일한 Benchmark 조건이 정의되어 있다.

실행할 때:
- 지원 Runtime에 Benchmark를 실행한다.

기대 결과:
- TTFT
- generation throughput
- VRAM 사용량
- model load time

항목을 기록하고 Runtime 간 결과를 비교할 수 있다.
```

## 범위

### 포함

* Windows 11 + WSL2 기반 실행 환경
* NVIDIA RTX 3090 GPU 추론
* llama.cpp baseline Runtime
* 로컬 LLM 모델 실행
* OpenAI-compatible API
* Streaming inference
* Coding Agent 연동
* Runtime 추상화 기준 수립
* 기본 Benchmark
* 환경설정 관리
* 기본 실행 및 종료 절차
* 로컬 네트워크 사용을 고려한 인터페이스 설계
* 향후 MacBook 클라이언트 연결을 고려한 구조

### 제외

* 상용 다중 사용자 서비스
* 인터넷 공개 LLM API
* Kubernetes 운영
* Multi-GPU inference
* 모델 Fine-tuning
* 자체 Foundation Model 학습
* 완전한 LLM Gateway 구현
* SGLang/vLLM 운영 적용
* macOS Runtime 구축
* 사용자 계정 및 과금 시스템
* 고가용성 구성

위 항목은 v0.1 완료 후 별도 요구사항으로 확장한다.

## 품질과 제약

* 보안:

  * LLM API를 인증 없이 Public Internet에 직접 노출하지 않는다.
  * 외부 장치 접근은 향후 VPN 또는 이에 준하는 안전한 사설 네트워크를 사용한다.
  * Agent의 shell 및 파일 수정 권한은 실행 프로젝트 범위를 고려하여 제한할 수 있어야 한다.

* 성능:

  * RTX 3090 GPU 가속이 정상적으로 적용되어야 한다.
  * Benchmark 결과를 통해 TTFT와 generation throughput을 측정할 수 있어야 한다.
  * Coding Agent 사용에 필요한 interactive inference가 가능한 수준인지 검증한다.

* 접근성:

  * CLI 기반으로 전체 환경을 실행할 수 있어야 한다.
  * 반복 실행을 위해 복잡한 수동 설정을 최소화한다.

* 호환성:

  * Windows 11 + WSL2 Ubuntu를 초기 기준 환경으로 한다.
  * NVIDIA CUDA 환경을 지원해야 한다.
  * 클라이언트는 가능한 한 OpenAI-compatible API에 의존한다.
  * 향후 macOS 클라이언트 연결이 가능해야 한다.

* 법률 및 규정:

  * 사용하는 모델과 Runtime의 라이선스를 확인한다.
  * 모델별 상업적 이용 및 재배포 조건을 문서화한다.

## 추적 관계

* 아키텍처:

  * [실행 구조](../architecture/localforge-runtime.md)

* ADR:

  * [baseline 결정](../decisions/ADR-001-inference-runtime-baseline.md)

* 명세:

  * [API 부분집합](../specs/inference-api.md)

* 작업:

  * [T001 진행 기록](../tasks/completed/T001-local-inference-baseline/README.md)

* 테스트:

  * Runtime smoke test
  * OpenAI-compatible API test
  * Streaming response test
  * GPU utilization verification
  * Coding Agent integration test
  * Runtime benchmark

## 미결 사항

* 초기 Local LLM 모델 및 quantization 확정
* llama.cpp 실행 방식을 native build와 container 중 어느 방식으로 표준화할지 결정
* 초기 context length 결정
* Coding Agent baseline을 OpenCode 또는 Aider 중 무엇으로 선정할지 결정
* LocalForge Gateway 도입 시점 결정
* SGLang/vLLM 비교 Benchmark 수행 시점 결정
* 향후 MacBook 접근을 위한 VPN 방식 결정
