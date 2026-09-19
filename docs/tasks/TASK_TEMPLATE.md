---
id: TASK-YYYYMMDD-001
title: 작업 제목
status: Proposed
owner: 담당자
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# 작업: 제목

## Status

`Proposed | Ready | In Progress | Blocked | Done | Cancelled` 중 하나를 사용합니다.

## Objective

이번 작업으로 달성할 관찰 가능한 결과를 작성합니다.

## Context

문제의 배경, 사용자 영향, 현재 상태를 작성합니다.

## Scope

- 작성 필요

## Out of Scope

- 작성 필요

## Requirements

- 요구사항:

## Implementation Plan

구현 순서, 영향을 받는 구성 요소와 전환 방식을 작성합니다.

## TODO Checklist

- [ ] 작은 검증 단위로 단계를 작성합니다.
- [ ] 각 단계에서 갱신할 코드와 문서를 연결합니다.

## 인수 조건

- [ ] 사용자 관점의 완료 조건을 작성합니다.

## Validation

- [ ] 단위 테스트
- [ ] 통합 또는 계약 테스트
- [ ] 정적 분석
- [ ] 수동 확인이 필요한 항목

## 외부 검토

규모 판정과 그 근거는 `Progress Notes`에 기록합니다. Small은 이 절을 `해당 없음 (Small)`으로 둡니다.

| 역할 | 수행 여부 | verdict | 결과 파일 |
|---|---|---|---|
| Planning Critic | 수행 / 생략 / `SKIPPED:<사유>` | `OK` 또는 `CONCERNS` | `active/reviews/<TASK-ID>/planning-01.json` |
| Independent Reviewer | 수행 / 생략 / `SKIPPED:<사유>` | `PASS` 또는 `FAIL` | `active/reviews/<TASK-ID>/review-01.json` |

`severity`가 `blocker` 또는 `high`인 finding은 전부 판정을 남깁니다. 기계적으로 반영하지 않으며, `REJECT`는 근거 없이 남기지 않습니다.

| Finding | 판정 | 근거 |
|---|---|---|
| F1 | `ACCEPT` / `REJECT` / `NEEDS_INVESTIGATION` | |

검토를 생략했거나 `SKIPPED`가 발생했으면 사유와 그때 무엇으로 대신했는지를 적습니다. 조용히 넘어가지 않습니다.

## 위험과 되돌리기

실패 가능성, 영향 범위, 안전하게 되돌리는 방법을 작성합니다.

## Related Documents

- 아키텍처:
- ADR 또는 RFC:
- 계약 명세:
- 운영 문서:

## Progress Notes

| 날짜 | 상태 | 내용 |
|---|---|---|
| YYYY-MM-DD | Proposed | 작업 문서 생성 |

## Completion Criteria

- [ ] 요구사항과 인수 조건을 충족합니다.
- [ ] 계획된 테스트와 검증을 통과합니다.
- [ ] 관련 Architecture, Spec, ADR과 운영 문서를 갱신했습니다.
- [ ] 남은 위험과 후속 작업을 기록했습니다.
- [ ] 상태를 `Done`으로 변경하고 `completed/` 이동 준비를 마쳤습니다.

## 완료 보고

- 변경 결과:
- 실행한 검증:
- 갱신한 문서:
- 남은 위험 또는 후속 작업:
