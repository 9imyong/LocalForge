---
id: T003
title: 한국어·코딩 응답 품질 평가 세트
status: Proposed
owner: 미정
created: 2026-09-19
updated: 2026-09-19
---

# 작업: 한국어·코딩 응답 품질 평가 세트

## Status

`Proposed`

## Objective

baseline 모델의 한국어·코딩 응답 품질을 **반복 실행 가능한 방식으로 측정**하고, 그 결과를 기록으로 남긴다. 지금은 품질에 대해 "합격을 주장하지 않는다"는 관찰만 있고 재현 가능한 근거가 없다.

## Context

T001에서 수동 확인 중 한국어 응답에 중국어 단어가 섞이는 현상을 관찰했으나, 측정 수단이 없어 관찰로만 남겼다.

- `docs/tasks/completed/T001-local-inference-baseline/README.md:46` — "수동 한국어·코딩 응답 확인, 일부 중국어 단어 혼입으로 품질 평가 후속 필요"
- `docs/operations/baseline-results.md:51` — "수동 한국어 설명에 중국어 단어 혼입 관찰: 한국어 품질 합격을 주장하지 않음"
- `docs/operations/baseline-results.md:52` — "비교 모델 및 한국어·코딩 평가 세트는 후속 작업"

측정 수단이 없어서 생기는 실질적 문제는 두 가지다. 모델이나 template을 바꿨을 때 품질이 나아졌는지 나빠졌는지 판단할 근거가 없고, 향후 비교 모델 도입 시 비교 기준이 없다.

`REQ-INFERENCE-001`은 TTFT·throughput 같은 성능 지표는 측정 가능하도록 요구하지만, 응답 품질에 대한 측정 요구는 없다. 이 작업은 그 공백을 메운다.

## Scope

- 한국어 응답과 코딩 응답에 대한 고정 프롬프트 세트 정의
- 그 세트를 실행해 결과를 파일로 남기는 실행 수단
- 판정 기준 정의 — 최소한 "한국어 응답 내 비한국어 문자 혼입"은 자동 판정 가능해야 한다
- 결과 기록 위치와 형식
- 실행 방법과 결과 해석 기준 문서화

## Out of Scope

- 모델 교체·비교 모델 도입 (이 작업은 **측정 수단**을 만드는 것이고 다른 모델과의 비교는 후속)
- Fine-tuning, template 재설계
- 코딩 응답의 정답 여부를 사람 없이 완전 자동 채점하는 것
- CI에서의 자동 실행 (로컬 GPU와 모델 파일이 필요하므로 이번 범위가 아니다)
- 성능(TTFT·throughput) 측정 — 이미 `scripts/smoke.py`가 한다

## Requirements

- 요구사항: [REQ-INFERENCE-001](../../requirements/REQ-INFERENCE-001.md) — 품질과 제약 절의 측정 가능성 요구를 응답 품질로 확장

## Implementation Plan

*(Main Codex가 작성한다. Planning Critic 검토 대상이다.)*

## TODO Checklist

- [ ] 작성 필요

## 인수 조건

- [ ] 한 번의 명령으로 평가 세트 전체를 실행할 수 있다.
- [ ] 실행 결과가 파일로 남고, 같은 조건에서 다시 실행해 이전 결과와 비교할 수 있다.
- [ ] 한국어 응답 내 비한국어 문자 혼입이 자동으로 판정되어 결과에 수치로 남는다.
- [ ] 모델·Runtime commit·실행 조건이 결과 파일에 함께 기록된다 — 조건이 다른 결과를 비교하는 것을 막는다.
- [ ] 사람이 판단해야 하는 항목은 자동 판정 항목과 **구분되어** 표시된다.
- [ ] 실행 방법과 결과 해석 기준이 운영 문서에 기록된다.

## Validation

- [ ] 평가 스크립트 자체의 단위 테스트 (판정 로직)
- [ ] 실제 baseline 서버 대상 1회 실행 및 결과 파일 확인
- [ ] 기존 `scripts/smoke.py` 회귀 없음
- [ ] Python·shell 구문 검사, 변경 문서 Markdown·링크 검사

## 외부 검토

*(규모 판정 후 기록한다.)*

| 역할 | 수행 여부 | verdict | 결과 파일 |
|---|---|---|---|
| Planning Critic | | | |
| Independent Reviewer | | | |

## 위험과 되돌리기

- 판정 기준을 잘못 잡으면 "측정은 되는데 쓸모없는 숫자"가 남는다. 특히 비한국어 문자 혼입은 코드 블록·고유명사·영문 기술 용어에서 정상적으로 발생하므로, 이를 혼입으로 세면 지표가 무의미해진다.
- 프롬프트 세트가 너무 적으면 실행마다 결과가 흔들려 비교가 불가능하다.
- 되돌리기: 새 파일 추가가 대부분이므로 해당 파일 삭제로 복구된다. 기존 `scripts/`와 `tests/`를 수정한 경우 그 커밋만 revert 한다.

## Related Documents

- 아키텍처: [LocalForge baseline 실행 구조](../../architecture/localforge-runtime.md)
- ADR: [ADR-001 baseline Runtime](../../decisions/ADR-001-inference-runtime-baseline.md), [ADR-003 tool calling template](../../decisions/ADR-003-tool-calling-template.md)
- 계약 명세: [추론 API 계약](../../specs/inference-api.md)
- 운영 문서: [baseline 측정 결과](../../operations/baseline-results.md)
- 선행 작업: [T001](../completed/T001-local-inference-baseline/README.md)

## Progress Notes

| 날짜 | 상태 | 내용 |
|---|---|---|
| 2026-09-19 | Proposed | 작업 문서 생성. T001·baseline-results의 후속 항목에서 도출 |
| 2026-09-19 | Proposed | 규모 판정: **작성 필요** (판정과 근거 한 줄을 Main Codex가 기록한다) |

## Completion Criteria

- [ ] 요구사항과 인수 조건을 충족합니다.
- [ ] 계획된 테스트와 검증을 통과합니다.
- [ ] 관련 Architecture, Spec, ADR과 운영 문서를 갱신했습니다.
- [ ] 외부 검토 결과와 finding 판정을 기록했습니다.
- [ ] 남은 위험과 후속 작업을 기록했습니다.
- [ ] 상태를 `Done`으로 변경하고 `completed/` 이동 준비를 마쳤습니다.

## 완료 보고

- 변경 결과:
- 실행한 검증:
- 갱신한 문서:
- 남은 위험 또는 후속 작업:
