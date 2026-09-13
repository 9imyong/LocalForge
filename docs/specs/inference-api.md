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
|---|---|
| GET /health | 200이면 준비 상태, 로딩 중 응답은 준비 완료로 처리하지 않음 |
| GET /v1/models | data 목록의 id에서 설정한 모델 별칭 확인 |
| POST /v1/chat/completions | model, messages, temperature, max_tokens, stream |
| streaming 옵션 | stream_options.include_usage=true |

- 일반 응답: choices[0].message.content의 비어 있지 않은 텍스트
- 스트리밍: SSE data JSON의 choices[].delta.content, finish_reason, 최종 `[DONE]`
- 토큰 수: usage.completion_tokens 사용, SSE 청크 수를 토큰 수로 사용 금지
- 연결·요청 타임아웃: 검증 클라이언트 120초, readiness 대기 기본 300초
- 호환성 범위: 위 부분집합만 검증, 전체 OpenAI 계약·Agent 도구 호출 호환 보장 제외
- health는 Runtime 운영용 경로이며 상위 Agent 필수 계약으로 고정하지 않음
- 예시 `api/openapi.yaml`은 기존 템플릿으로 본 서버의 실제 계약이 아님
