---
id: T003
title: 한국어·코딩 응답 품질 평가 세트
status: Done
owner: Main Codex
created: 2026-09-19
updated: 2026-09-20
---

# 작업: 한국어·코딩 응답 품질 평가 세트

## Status

`Done`

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

1. 고정 JSON 평가 세트 추가: 한국어 설명·요약·지시 준수 4건, Python 구현·버그 수정 4건. 각 사례에 ID·prompt·수동 판정 기준 명시.
2. 표준 라이브러리 기반 `scripts/quality-eval.py`와 `.env` 로딩 wrapper, `make quality-eval` 추가. 기존 HTTP API 사용, 응답 코드 실행 금지, 요청별 오류·빈 응답·잘림 기록, 모든 사례 실행 후 하나라도 실패하면 종료 코드 1.
3. 한국어 산문에서 fenced/inline code를 제외하고 Hangul·Latin·기타 Unicode 문자 수 집계. 숫자·구두점·공백·기호·결합 부호는 집계 제외. Latin 문자는 별도 수치로 표시하고 CJK·가나 등 기타 문자는 혼입 후보로 표시. 언어 식별·정답 판정과 구분하고 코드만 있는 응답은 자동 합격 처리 금지.
4. 모델 revision·SHA256, Runtime commit/image, context·GPU layers, template SHA256, 세트 SHA256, seed·temperature·max_tokens·동시성·판정 버전을 결과에 기록. 서버 실행 구성과 일치 여부 확인, 내장 template은 source=builtin 및 서버가 제공한 template의 SHA256 기록. 기본 출력은 실행별 고유 파일. 비교 명령은 조건 fingerprint 불일치·불완전 결과를 거부.
5. 판정 경계값, 조건 변경 비교 거부, 응답 실패·잘림, 전체 실행·결과 기록을 unit/mock HTTP 테스트로 검증. 기존 smoke 회귀 테스트 및 구문 검사 수행.
6. 실제 baseline 전체 평가 1회 및 기존 smoke 실행. 운영 안내·요구사항·현재 구조·CHANGELOG 갱신, Markdown·링크 검사 수행.
7. Planning/Independent 양쪽 스키마 검증 및 모든 finding 판정·집계 기록. 테스트 통과 후에만 Independent Reviewer 호출, 완료 기준 충족 시 Task와 reviews/T003 함께 completed 이동.

## TODO Checklist

- [x] 고정 평가 세트와 실행·비교 수단 구현
- [x] 자동 문자 집계와 수동 판정 분리
- [x] unit/mock·실제 baseline·회귀 검증
- [x] 운영 문서와 요구사항·구조 갱신
- [x] 양쪽 외부 검토·판정 기록 및 완료 이동

## 인수 조건

- [x] 한 번의 명령으로 평가 세트 전체를 실행할 수 있다.
- [x] 실행 결과가 파일로 남고, 같은 조건에서 다시 실행해 이전 결과와 비교할 수 있다.
- [x] 한국어 응답 내 비한국어 문자 혼입이 자동으로 판정되어 결과에 수치로 남는다.
- [x] 모델·Runtime commit·실행 조건이 결과 파일에 함께 기록된다 — 조건이 다른 결과를 비교하는 것을 막는다.
- [x] 사람이 판단해야 하는 항목은 자동 판정 항목과 **구분되어** 표시된다.
- [x] 실행 방법과 결과 해석 기준이 운영 문서에 기록된다.

## Validation

- [x] 평가 스크립트 자체의 단위 테스트 (판정 로직)
- [x] 실제 baseline 서버 대상 1회 실행 및 결과 파일 확인
- [x] 기존 `scripts/smoke.py` 회귀 없음
- [x] Python·shell 구문 검사, 변경 문서 Markdown·링크 검사

### 실행 근거

- `make test`: 기존 9개 + 신규 18개, 총 27개 통과 (외부 리뷰 후 경계값 보완 포함)
- `make quality-eval`: 8/8 수집 완료, `.local/results/quality/20260920T122101-0d70e26b.json`
- 동일 조건 재실행: `.local/results/quality/t003-repeat.json`, 8/8 완료
- `--compare`: 조건 일치 확인 및 사례별 차이 출력, `.local/results/quality/t003-comparison.json`
- 실제 관찰: 첫 실행 `ko-instructions` 산문에서 키릴 문자 5개 검출, 품질 합격 주장 없음
- 구현 후 `bash scripts/smoke.sh --runs 1 --output .local/results/t003-smoke-after.json`: 통과
- Python·shell 구문 및 변경 문서 Markdown·내부 링크 검사 통과 (최종 이동 후 재검사 예정)
- 평가기 첫 실제 실행에서 template 최종 LF 차이 확인·보완, 단위 테스트 추가 후 재실행 성공
- API 계약·채택 ADR 변경 없음. 품질 요구사항과 현재 구조·운영 안내·CHANGELOG 갱신

## 외부 검토

Planning context에 대화 이력 유입 0건. planning-02 structured_output의 JSON Schema 검증 통과. 첫 실패를 포함한 호출 2건 metrics 기록.

| 역할 | 수행 여부 | verdict | 결과 파일 |
| --- | --- | --- | --- |
| Planning Critic | 수행 (첫 타임아웃 후 재시도) | CONCERNS | `reviews/T003/planning-02.json` |
| Independent Reviewer | 수행 | PASS | `reviews/T003/review-01.json` |

### Finding 판정

| 역할/번호 | 등급 | 판정 | 근거 및 반영 |
| --- | --- | --- | --- |
| planning F1 | high | ACCEPT | 숫자·구두점·공백·기호·결합 부호 제외, Unicode 문자 범주만 집계 및 단위 테스트 |
| planning F2 | medium | ACCEPT | 개별 실패 저장 후 전체 사례 실행, 마지막에 실패 종료 및 비교 거부 |
| planning F3 | low | ACCEPT | 내장 template은 source=builtin, 실제 서버 template 해시로 fingerprint 구성 |
| review F1 | low | ACCEPT | Cmd 마지막 옵션 값 누락 방어 및 구성 오류 단위 테스트 추가, 27개 테스트 통과 |
| review F2 | low | REJECT | 수정 문서의 markdownlint MD060 통과에 필요한 표 공백 정리. 내용 변화 없으며 별도 분리하지 않음 |

### P1.5 검증과 실제 마찰 지점

- 양쪽 context: 저장소 발췌·diff·검증 사실만 조립, 대화 이력 유입 0건. 전송 원문은 `reviews/T003/*-context.txt`, 크기·SHA256은 `context-audit.json`
- 양쪽 `structured_output`: 각 역할 JSON Schema 검증 통과. Planning CONCERNS·3건, Independent PASS·2건
- 호출 행 3개: planning SKIPPED:api-error 1회 + planning 성공 1회 + review 성공 1회
- disposition 행 2개: planning 3/0/0, review 1/1/0 (ACCEPT/REJECT/NEEDS_INVESTIGATION)
- acceptance rate: 4 / 5 = **80%**, 미해결 0건. 단일 Task이므로 reviewer 유효성·routing 변경 근거로 확대 해석 금지
- 첫 Planning API 타임아웃으로 harness 차단 1회. 권한 확장 재시도로 성공; 원인이 샌드박스 네트워크였다고 확정하지 않음
- timeout 분류: CLI 내부 `Request timed out`은 `SKIPPED:api-error`, wrapper의 제한 시간 초과와 구분됨. 실패 raw의 duration_ms=178339·cost=0이 metrics에서는 null로 손실되는 점 관찰
- 실패 직후 자체 계획 검토 및 동일 pack 재시도, 미검증 상태로 구현 관문을 건너뛰지 않음. 총 차단 1회로 사용자 중단 기준 3회 미도달
- Independent의 표 서식 지적은 코드 결함이 아닌 스타일 의견이며, 프롬프트의 스타일 취향 지적 제외 규칙과 어긋난 사례로 기록
- 리뷰 후 low 경계값 수정은 Main Codex가 직접 확인, 재호출 없이 관련 테스트 포함 27개 통과
- Reviewer의 실제 GPU 재현·원문 혼입 검출 확인 한계는 주 세션의 실제 실행 결과와 로컬 원본으로 보완
- P2 문서 선작성 없음. 원본 응답·metrics·위 관찰 사실을 후속 검토 자료로 보존

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
| --- | --- | --- |
| 2026-09-19 | Proposed | 작업 문서 생성. T001·baseline-results의 후속 항목에서 도출 |
| 2026-09-19 | Proposed | 규모 판정: **Medium** — 새 기능 및 새 테스트 전략 필요. P1.5에서 양쪽 역할 검증을 위해 Planning Critic 수행 |
| 2026-09-20 | In Progress | 계획 작성 및 Planning Critic 호출. 첫 호출 Request timed out → SKIPPED:api-error, harness 차단 1회. 동일 pack으로 권한 확장 재시도 |
| 2026-09-20 | In Progress | 기존 unit 9개 통과. 정지된 baseline 컨테이너 시작 후 smoke 1회 통과. 기존 start-time 파일은 이전 기동 값이므로 이번 start-to-ready 수치는 해석 제외 |

| 2026-09-20 | Done | 구현·검증·양쪽 외부 검토 및 판정 완료. P1.5 기능 검증 통과, Task와 reviews/T003 함께 completed 이동 |

## Completion Criteria

- [x] 요구사항과 인수 조건을 충족합니다.
- [x] 계획된 테스트와 검증을 통과합니다.
- [x] 관련 Architecture, Spec, ADR과 운영 문서를 갱신했습니다.
- [x] 외부 검토 결과와 finding 판정을 기록했습니다.
- [x] 남은 위험과 후속 작업을 기록했습니다.
- [x] 상태를 `Done`으로 변경하고 `completed/` 이동 준비를 마쳤습니다.

## 완료 보고

- 변경 결과: 고정 평가 8건·실행·조건 비교·문자 후보 집계 제공, T003 및 리뷰 기록 completed 이동
- 실행한 검증: unit 27개, 실제 평가 8건 × 2회·조건 비교, 기존 smoke, 구문·Markdown·내부 링크 검사
- 갱신한 문서: README·REQ-INFERENCE-001·현재 구조·품질 운영 안내·baseline 결과·CHANGELOG
- 남은 위험 또는 후속 작업: 수동 품질 판정 pending, 작은 세트의 대표성 한계. P2는 실제 관찰 기반 후속 검토. 작업 전 정지 상태였던 baseline 컨테이너는 검증 후 정지 복원
