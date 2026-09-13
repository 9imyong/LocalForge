# C4 Container Diagram

## 문서 목적

시스템 내부의 주요 실행·배포 단위와 데이터 저장소, 외부 관계를 보여줍니다. 각 단위의 책임은 [구성 요소](../../building-blocks.md)에 기록합니다.

## 언제 수정하는가

Container를 추가·분리·통합하거나 주요 통신 관계 또는 기술 경계가 바뀔 때 수정합니다.

## 작성할 내용

- 사용자 접점, 서비스, 작업 프로세스, 데이터 저장소
- Container 사이의 관계와 통신 목적
- 이해에 필요한 최소한의 기술 정보

## 최소 예제

```mermaid
flowchart LR
    사용자[사람: 사용자]
    웹[Container: 사용자 애플리케이션]
    API[Container: 응용 서비스]
    DB[(Container: 데이터 저장소)]
    사용자 -->|사용한다| 웹
    웹 -->|요청한다| API
    API -->|읽고 쓴다| DB
```

## 관련 문서

- [구성 요소](../../building-blocks.md)
- [배포 구조](../../deployment.md)
- [C4 안내](README.md)
