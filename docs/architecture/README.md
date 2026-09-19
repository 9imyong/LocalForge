# 아키텍처 안내

이 디렉터리는 시스템의 **현재 구조**를 설명하는 기준 문서입니다. standard 티어는 arc42의 관점을 참고하되 문서를 쪼개지 않고 한 문서로 관리합니다. 이 저장소에서는 [LocalForge baseline 실행 구조](localforge-runtime.md)가 그 문서입니다. 결정의 역사와 근거는 [ADR](../decisions/README.md)에 기록합니다.

## 문서 목적

Architecture 문서의 책임, 갱신 시점, 분리 기준 안내.

## 언제 수정하는가

- 시스템 경계, 구성 요소, 실행 흐름, 배포, 데이터 구조 변경 시
- 품질 목표, 공통 설계 원칙, 알려진 위험 변경 시

## 문서 구성

- [LocalForge baseline 실행 구조](localforge-runtime.md): **이 저장소의 현재 구조 기준 문서**
- `ARCHITECTURE_TEMPLATE.md`: 통합 아키텍처 문서 양식. `localforge-runtime.md`가 담지 못하는 관점(품질 목표, 공통 설계 원칙 등)이 필요해지면 이 양식으로 확장

## 적용과 갱신 원칙

- **동시 갱신 필수:** 코드나 배포 상태 변경으로 현재 구조 설명이 달라지는 경우, 같은 변경 묶음에서 문서 갱신
- **공백 처리:** 해당하지 않는 관점은 내용을 만들지 않고 `해당 없음`과 사유 기록
- **중복 금지:** 결정 이유를 Architecture에 복제하지 않고 관련 ADR 링크

## full 티어로 넘어가는 시점

다음 중 하나에 해당하면 원본 템플릿 저장소(`project-sample`)의 `templates/full/docs/architecture/`에서 개별 관점 문서와 C4 다이어그램을 가져와 분리합니다.

- 통합 문서 하나가 너무 길어져 관점별로 담당자가 갈리는 경우
- 외부 팀에 시스템 경계를 설명할 다이어그램이 반복적으로 필요한 경우
- 배포 토폴로지나 데이터 흐름이 문단 설명으로 감당되지 않는 경우

## 관련 문서

- [문서 운영 정책](../DOCS_GOVERNANCE.md)
- [요구사항](../requirements/README.md)
- [ADR](../decisions/README.md)
