---
id: ADR-002
status: 채택
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# ADR-002: OpenCode 로컬 provider와 fixture 격리

## 맥락

- 사용자 요청: OpenCode를 최초 Coding Agent 연동 대상으로 사용
- 기존 T001 baseline 유지 및 상위 Agent와 Runtime의 직접 결합 방지 필요
- 모델 생성 명령의 호스트 프로젝트·개인 파일 접근 위험

## 결정

- OpenCode 1.18.30과 npm lockfile을 통한 로컬 설치
- `@ai-sdk/openai-compatible` provider로 기존 HTTP API 연결
- 기본 모델 및 보조 모델 모두 LocalForge 별칭 사용, 외부 provider 미사용
- CLI 실행용 컨테이너에 별도 fixture만 작업공간으로 마운트
- Agent 구성은 도구 권한과 짧은 prompt로 제한, Agent 소스·Gateway 구현 없음
- 실제 도구 이벤트·테스트·파일 차이를 함께 검사하는 smoke로 성공 여부 판정
- tool calling 미성공 시 실패 기록 및 Task active 유지, 모델 임의 교체 금지

## 대안과 결과

| 대안 | 판단 |
| --- | --- |
| 호스트 프로젝트에 직접 실행 | 검증 전 변경 범위 확대 위험으로 미채택 |
| 별도 Agent 또는 Gateway 개발 | 범위 제외, 표준 provider 사용 |
| 도구 호출 형태의 텍스트를 임의 실행 | 실행 계약 훼손 및 잘못된 성공 판정 위험으로 미채택 |
| 모델 교체 또는 T001 template 변경 | 사용자 제약에 따라 이번 작업에서 미실행 |

- 채택 범위: 연결·설치·검증 구성, 모델의 Coding Agent 적합성 채택 아님
- 현재 실제 Agent E2E 실패, [검증 결과와 후속 과제](../operations/opencode.md) 참조
- host network로 loopback API 사용 가능, 네트워크 격리까지 보장하지 않음
