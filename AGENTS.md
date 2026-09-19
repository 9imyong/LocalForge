# AI 에이전트 작업 규칙

## 기본 원칙

1. 작업 전에 `README.md`, 관련 요구사항, 현재 아키텍처를 확인한다.
2. 현재 상태는 아키텍처 문서, 결정의 이유는 ADR을 기준으로 판단한다.
3. 기존 변경을 임의로 되돌리거나 관련 없는 파일을 수정하지 않는다.
4. 비밀 값, 개인정보, 내부 접근 주소를 문서나 로그에 기록하지 않는다.
5. 코드와 문서가 함께 바뀌어야 하는 경우 같은 변경 묶음에서 갱신한다.
6. 문서 작성·수정 시 [문서 작성 스타일](docs/DOCS_GOVERNANCE.md#문서-작성-스타일) 준수.

## 표준 작업 순서

1. 저장소 루트의 `AGENTS.md`를 확인한다.
2. `docs/requirements/`에서 관련 Requirement를 확인한다.
3. `docs/architecture/`에서 현재 구조와 제약을 확인한다.
4. `docs/decisions/`에서 관련 ADR과 이미 내려진 결정의 근거를 확인한다.
5. `docs/tasks/active/`에서 기존 작업과 충돌 또는 중복 여부를 확인한다.
6. 작업 규모가 기준에 해당하면 새 Task를 만들거나 기존 Task를 갱신한다.
7. 합의된 범위 안에서 구현한다.
8. 관련 테스트, 정적 분석, 문서 검증을 수행한다.
9. Task가 있으면 진행 기록과 검증 결과를 갱신한다.
10. 실제 변경을 기준으로 Architecture와 ADR 갱신 필요 여부를 다시 확인한다.
11. 완료 조건을 충족한 Task는 `docs/tasks/completed/`로 이동하고 필요한 CHANGELOG를 갱신한다.

`docs/specs/`, `docs/rfcs/`, `docs/operations/`가 이 저장소에 있으면 각각 계약 확인, 사전 제안, 운영 절차 갱신 단계를 위 순서에 추가한다.

## 작은 변경의 예외

다음 조건을 모두 만족하면 별도 Requirement, ADR 또는 Task를 만들지 않아도 된다.

- 한두 파일에 국한된 명백하고 짧은 수정이다.
- 기존 요구사항과 아키텍처 결정을 변경하지 않는다.
- 외부에 노출되는 동작과 인터페이스를 변경하지 않는다.
- 별도의 진행 상태나 인수인계 기록이 필요하지 않다.

예외를 적용해도 관련 테스트와 문서 영향 확인은 수행한다. 기존 Task가 있으면 같은 목적의 새 Task를 만들지 않는다. 문서가 없다는 이유만으로 현재 작업 범위를 임의로 확대하지 않는다.

## 외부 검토

구현 전 계획과 구현 후 diff를 외부 검토자(Claude)에게 보낸다. 최종 결정권은 이 저장소에서 작업하는 주 세션에 있다.

### 규모 판정

변경의 **성격**으로 판정한다. 파일 개수는 기준이 아니다.

| 규모 | 조건 | Planning Critic | Independent Reviewer |
|---|---|---|---|
| Small | 국소 변경이고 계약·데이터 구조·보안·실행 구조가 모두 불변이며 기존 테스트로 검증 가능 | 생략 | 생략 |
| Medium | 새 기능, 여러 구성 요소에 영향, 내부 interface 변경, 새 테스트 전략 필요, regression 가능성 중 하나 이상 | 위험이 있을 때만 | 수행 |
| Large | 아키텍처 변경, 인증·보안, 실행·배포 구조, 추론 파이프라인, 되돌리기 어려운 변경 중 하나 이상 | 수행 | 수행 |

판정 결과와 근거 한 줄을 Task 문서 `Progress Notes`에 남긴다. 애매하면 상위로 올린다.

### 호출

```bash
/home/joon/code/agent-harness/bin/claude-review.sh plan|review \
  --task <TASK-ID> --project /home/joon/code/LocalForge --context <pack.md>
```

context pack은 Markdown 파일 하나로 조립한다. 양식은 `agent-harness/DESIGN.md` §5.1. 대화 이력은 전달하지 않고, 파일 전체 대신 발췌와 `path:line`을 쓴다. 상한은 40KB(soft) / 80KB(hard)이고, 넘으면 발췌를 줄이거나 Task를 쪼갠다.

종료 코드: `0` 지적 없음, `1` 지적 있음(실패 아님), `2` `SKIPPED:<사유>`, `3` 사용법 오류.

### 판정과 기록

- `blocker`·`high` finding은 전부 `ACCEPT` / `REJECT` / `NEEDS_INVESTIGATION` 판정을 Task 문서 `## 외부 검토` 절에 남긴다. 기계적으로 전부 반영하지 않는다.
- 판정 집계는 `reviews/<TASK-ID>/metrics.jsonl`에 반영한다.
  `/home/joon/code/agent-harness/bin/record-disposition.sh <reviews-dir> <role> <accepted> <rejected> <needs_investigation>`
- 역할별 호출은 Task당 **최대 2회**. 3회째가 필요하면 직접 판단하고 그 사실을 기록한다.
- 테스트가 실패한 상태로 `review`를 보내지 않는다.
- `SKIPPED`가 나오면 자체 검토로 진행하되, 사유와 대체 수단을 Task 문서와 사용자 보고 양쪽에 남긴다. **검토 생략을 조용히 넘어가지 않는다.**

## 문서 갱신 기준

- 동작이나 성공 조건 변경: 요구사항 갱신
- 현재 구조 변경: 아키텍처 갱신
- 중요한 선택과 대안 확정: ADR 추가
- 여러 모듈에 걸친 장기 작업: 작업 문서 작성

구체적인 생성·생략 기준은 `docs/DOCS_GOVERNANCE.md`를 따른다.

## 검증과 완료 조건

- 관련 테스트, 정적 분석, 문서 링크 검사를 실행한다.
- 실행하지 못한 검증은 이유와 위험을 명시한다.
- 완료된 작업 문서는 `docs/tasks/completed/`로 이동한다.
- ADR은 승인 후 내용을 덮어쓰지 않고, 변경이 필요하면 새 ADR로 대체 관계를 기록한다.
