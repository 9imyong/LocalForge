---
status: 현재
owners: [담당 팀]
last_reviewed: YYYY-MM-DD
---

# 구성 요소

## 문서 목적

시스템을 이루는 주요 실행 단위와 선택적으로 그 내부 구성 요소의 책임, 경계, 의존 방향을 설명합니다.

## 언제 수정하는가

- 실행 또는 배포 단위를 추가·분리·통합할 때
- 구성 요소의 책임이나 소유 데이터가 달라질 때
- 허용되는 의존 방향이나 내부 경계가 바뀔 때

## 작성할 내용

- 구성 요소별 책임과 소유 팀
- 제공하거나 소비하는 인터페이스
- 소유 데이터와 의존 대상
- 허용하거나 금지하는 의존 방향

## 최소 예제

| 구성 요소 | 책임 | 소유 데이터 | 의존 대상 |
|---|---|---|---|
| 사용자 진입점 | 요청 수신과 응답 | 없음 | 응용 서비스 |
| 응용 서비스 | 업무 규칙 수행 | 작성 필요 | 저장소, 외부 연동 |

정식 시각화는 [C4 Container](diagrams/c4/container.md), 복잡한 실행 단위의 내부는 필요할 때만 [C4 Component](diagrams/c4/component.md)에 작성합니다.

## 의존성 규칙

- 허용되는 의존 방향과 금지되는 결합을 작성합니다.
- 구성 요소 사이의 계약은 [기술 명세](../specs/README.md)를 링크합니다.

## 관련 문서

- [해결 전략](solution-strategy.md)
- [C4 Container](diagrams/c4/container.md)
- [C4 Component](diagrams/c4/component.md)
- [실행 흐름](runtime.md)
- [배포 구조](deployment.md)
