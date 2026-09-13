---
id: ADR-003
status: 채택
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# ADR-003: 현재 모델의 도구 호출 template 호환성

## 맥락

- T002에서 모델이 도구 호출을 일반 텍스트로 생성하여 Agent 실행 차단
- 사용자 요청: 현재 모델과 llama.cpp 버전을 유지하며 template·parser·API 계층 분리 진단 및 해결
- 직접 API와 native completion에서도 기존 호출 태그와 다른 출력 확인

## 결정

- 모델 가중치·revision·SHA256 및 llama.cpp commit 유지
- 도구 호출 지시와 assistant tool-call 직렬화를 JSON code fence로 일치시킨 별도 Jinja template 사용
- Runtime의 기존 자동 parser에서 표준 `message.tool_calls` 및 SSE delta로 변환
- 상위 Agent에서 content를 도구로 재해석하는 코드·proxy·Gateway 미도입
- `CHAT_TEMPLATE_FILE` 설정 및 읽기 전용 마운트로 적용, 빈 값으로 T001 내장 template 복원 가능
- 직접 도구 계약 검증을 `make tool-smoke`로 제공
- OpenCode는 context 4096에 맞춰 read·edit·bash 도구 사용, ls·grep은 bash 실행으로 검증
- OpenCode 모델 capability에 temperature 지원을 명시하여 설정한 temperature=0 전달

## 대안과 결과

| 대안 | 관찰 및 판단 |
| --- | --- |
| GGUF 내장 template | 직접 API auto/required 호출에서 tool_calls 미수신 |
| 공식 Qwen template만 적용 | 이중 중괄호 차이 수정만으로 해결되지 않음 |
| chatml fallback | 현 고정 버전에서 도구 없는 prompt로 처리, 미채택 |
| tools XML 태그 일치 | 간단한 직접 도구 호출 성공, OpenCode 조건에 따른 JSON fence 출력은 여전히 미처리 |
| JSON code fence 직렬화 | 직접 API 계약과 OpenCode 실제 도구 동작 확인, 채택 |
| 모델 교체·Runtime 업데이트 | 이번 범위에서 미실행 |

- 모델 자체가 도구 호출을 전혀 못한다는 결론은 기각, 범용 Coding 성능 검증으로 확대 해석 금지
- 기존 template의 형식과 관측된 모델 출력의 불일치가 최초 차단 원인
- 이후 Agent context·종료 제어 문제는 template/parser 문제와 구분
- ADR-001의 Runtime·가중치·API 경계 유지, ADR-002의 설치·격리 구성 유지
- 상세 근거 및 운영 절차: [Tool Calling 검증](../operations/tool-calling.md)
