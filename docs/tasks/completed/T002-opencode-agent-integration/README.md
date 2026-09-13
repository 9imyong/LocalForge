---
id: T002
title: OpenCode Agent Integration 및 Tool Calling Compatibility
status: Done
created: 2026-09-13
updated: 2026-09-13
---

# T002: OpenCode Agent Integration

- 결과: OpenCode 설치·연결 및 제한된 fixture Coding Agent E2E 검증 완료
- 최초 Blocked 원인: 모델 생성 형식과 template 호출 직렬화의 불일치
- 후속 사용자 요청에 따라 Tool Calling Compatibility 진단·해결 포함
- 유지: 가중치·모델 revision·SHA256, llama.cpp commit, GPU layer, context 4096
- 변경: Runtime Jinja template override 및 OpenCode 최소 도구 구성·temperature capability·10단계 한도

## 기준 및 범위

- [요구사항](../../../requirements/REQ-INFERENCE-001.md): 05·13·14
- [아키텍처](../../../architecture/localforge-runtime.md), [API 계약](../../../specs/inference-api.md)
- 포함: 설치·격리 실행·직접 API 도구 진단·실제 fixture 도구 실행·회귀 검증·문서
- 제외: 모델 교체·학습, Runtime 업데이트, Gateway·Web UI·외부 공개

## 완료 조건

- [x] OpenCode 1.18.30의 재현 가능한 설치 및 버전 기록
- [x] localforge provider 및 기본·보조 모델 선택
- [x] 일반 응답 및 OpenCode SSE 텍스트 delta 확인
- [x] Agent의 실제 저장소 탐색·파일 읽기·코드 검색
- [x] Agent의 실제 허용 shell 및 파일 수정 도구 실행
- [x] 수정 전 실패 테스트 관찰·원인에 해당하는 최소 수정
- [x] Agent의 테스트 재실행 통과 및 git diff 확인
- [x] 최소 1건의 Coding Agent fixture E2E 및 종료 코드 0
- [x] 동일 구간의 inference 요청 처리와 GPU 사용 증거
- [x] calculator.py 외 파일의 의도하지 않은 변경 없음 확인
- [x] 직접 API auto·required·이름 지정·SSE·none 및 tool 결과 회신 검증
- [x] 모델 해시·Runtime commit 보존 및 일반 inference 회귀 확인
- [x] secret·모델·binary·세션의 Git 제외
- [x] 설치·실행·검증·되돌리기 및 남은 제약 문서화
- [x] Architecture·Spec·ADR 갱신 확인
- [x] Done 전환 및 completed 이동

## 검증 결과

- 기본 서버 E2E: `20260913T122518925255Z`, 모든 행동 조건 및 harness 통과
- 실제 도구: bash의 실패 unittest·ls·grep·성공 unittest·git diff, read, edit
- 실제 수정: calculator.py의 차 연산을 합 연산으로 변경
- 검증 근거: 원시 tool_use 이벤트, 수정 전후 테스트, 파일 해시, diff, GPU 및 서버 로그
- 직접 도구 검사: 5조건 통과, tool 결과 5 회신 후 텍스트 종료
- 단위 테스트: 9개 통과
- Python·shell 구문 및 변경 문서 Markdown·로컬 링크 검사: 통과
- 상세 수치·재현 명령: [Tool Calling 결과](../../../operations/tool-calling.md)

## 진행 기록

- 2026-09-13: OpenCode 설치·로컬 provider·일반 응답·SSE 완료
- 2026-09-13: 도구 대신 JSON 텍스트 반환, 최초 E2E 실패로 Blocked
- 2026-09-13: 사용자 후속 요청에 따라 직접 API·template·parser 계층 진단 재개
- 2026-09-13: native completion에서도 호출 태그 불일치 확인, template 형식 통일로 직접 API 해결
- 2026-09-13: OpenCode 실제 도구 실행 이후 context·불필요한 반복 호출 문제 확인
- 2026-09-13: 3종 도구 및 10단계 한도로 모든 fixture 행동 확인
- 2026-09-13: 기본 서버 적용·직접 API·E2E·회귀 검사 완료, Done

## 남은 위험과 완료 범위

- 완료 범위: 작은 fixture의 관측 가능한 도구 실행 통합, 범용 자율 코딩 품질 아님
- 마지막 응답은 최대 단계 안내, 자연스러운 결과 요약 품질은 후속 과제
- 큰 저장소·장기 대화에는 context 및 단계 한도 재검토 필요
- 단계 제한 없는 시도에서 git diff 반복 및 stage/commit 시도 관측, stage/commit은 권한 거부
- 복잡한 도구 schema·병렬 호출의 일반적인 정확성은 미검증
- 실제 작업 판정은 모델의 완료 주장 대신 도구 이벤트와 독립 검증 사용
- 되돌리기: CHAT_TEMPLATE_FILE 빈 값 및 서버 재기동, 기존 tool 실패 재발 가능

## 결정 및 운영

- [ADR-002: 설치·격리](../../../decisions/ADR-002-opencode-integration.md)
- [ADR-003: 도구 호환성](../../../decisions/ADR-003-tool-calling-template.md)
- [OpenCode 실행](../../../operations/opencode.md)
