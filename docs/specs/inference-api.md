---
status: 현재
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# Baseline inference API

- 기본 주소: `http://127.0.0.1:18000`, 설정의 PORT로 변경 가능
- 모델 별칭: `localforge-baseline`, MODEL_ALIAS로 변경 가능
- 모델·정밀도·GPU 관련 llama.cpp 옵션은 서버 실행 구성에만 사용

| 요청 | 사용 계약 |
| --- | --- |
| GET /health | 200이면 준비 상태, 로딩 중 응답은 준비 완료로 처리하지 않음 |
| GET /v1/models | data 목록의 id에서 설정한 모델 별칭 확인 |
| POST /v1/chat/completions | model, messages, temperature, max_tokens, stream |
| streaming 옵션 | stream_options.include_usage=true |

- 일반 응답: choices[0].message.content의 비어 있지 않은 텍스트
- 스트리밍: SSE data JSON의 choices[].delta.content, finish_reason, 최종 `[DONE]`
- 토큰 수: usage.completion_tokens 사용, SSE 청크 수를 토큰 수로 사용 금지
- 연결·요청 타임아웃: 검증 클라이언트 120초, readiness 대기 기본 300초
- 호환성 범위: 문서화한 부분집합만 검증, 전체 OpenAI 계약 및 모든 Agent 작업 호환 보장 제외
- health는 Runtime 운영용 경로이며 상위 Agent 필수 계약으로 고정하지 않음
- 예시 `api/openapi.yaml`은 기존 템플릿으로 본 서버의 실제 계약이 아님

## 도구 호출 부분집합

- 요청: tools 배열의 type=function, function.name·description·parameters
- 선택: tool_choice=auto, required, none 및 function 이름 지정
- 일반 호출 응답: choices[0].finish_reason=tool_calls, message.tool_calls 배열
- 호출 원소: 비어 있지 않은 id, type=function, function.name, JSON 문자열 function.arguments
- content가 비어 있는 정상 도구 호출 허용
- SSE 호출 응답: delta.tool_calls의 index별 id·type·function.name·arguments 조립
- SSE 완료: finish_reason=tool_calls와 최종 DONE 필수, 청크 하나를 완성된 arguments로 간주 금지
- 도구 회신: assistant의 tool_calls 이력 뒤 role=tool, 동일 tool_call_id, 문자열 content 전달
- none: 실행 가능한 tool_calls 없음, content의 JSON 모양 텍스트를 직접 실행하는 fallback 금지
- 검증: 단일 add(a=2,b=3), 결과 5 회신 후 정상 텍스트 종료 및 OpenCode fixture
- 복잡한 schema·여러 병렬 함수·모든 모델의 tool_choice 준수는 미검증
- tool 호출의 실제 실행 권한과 인자 검증은 클라이언트 책임
- Runtime의 template 경로·호출 직렬화 문법은 상위 API 계약에서 제외
- 재현: make tool-smoke, [호환성 결과](../operations/tool-calling.md)
