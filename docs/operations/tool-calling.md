---
status: 현재
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# Tool Calling 호환성 진단과 해결

- 결과: 현재 가중치·llama.cpp commit·context 4096을 유지하며 직접 API 및 OpenCode fixture E2E 통과
- 수정 계층: Chat Template의 호출 지시·직렬화 형식, OpenCode 도구 구성·temperature capability·단계 한도
- 미변경: 모델 파일, 모델 revision, Runtime 소스, API 변환 코드, parser 소스, GPU 설정
- 기본 서버: `CHAT_TEMPLATE_FILE=configs/llama/qwen25-tools.jinja` 적용

## 계층별 판별

| 계층 | 관측 및 판단 |
| --- | --- |
| OpenCode | 미사용 직접 API에서도 최초 실패 재현, 최초 원인의 필수 조건 아님 |
| API 변환 | template 변경 후 동일 Chat Completions 경로에서 정상 tool_calls 수신, 변환 코드 수정 불필요 |
| llama.cpp 실행 옵션 | 기존 jinja 기본 활성화, 단순 flag 누락이 원인 아님; 현재는 명시적으로 --jinja 사용 |
| Chat Template | 내장 예제의 이중 중괄호 및 모델이 생성하는 호출 형식과의 불일치 확인 |
| Tool Parser | native completion도 기존 기대 태그를 생성하지 않음; 출력 형식을 일치시키면 기존 parser로 정상 변환 |
| Local LLM | 같은 가중치로 add 함수·인자 선택, tool 결과 반영, 실제 파일 수정 가능; 도구 호출 불가능 모델로 단정 불가 |

- 원인 범위: 이 고정 GGUF와 기존 template 조합에서 호출 형식 불일치
- 모델이 특정 태그를 선호하는 학습상 원인까지 규명한 결과는 아님
- 범용 모델 품질·다른 양자화·다른 Runtime에 대한 결론으로 확대 해석 금지

## 비교 실험

| 구성 | 직접 API / OpenCode 결과 |
| --- | --- |
| 내장 template | auto·required에서 tool_calls 없이 content 출력 |
| 공식 Qwen template | 중괄호 수정 후에도 tools XML 텍스트 반환 |
| native completion | Chat API 우회 시에도 tools XML 출력, API parser가 올바른 태그를 단순 유실한 현상으로 보기 어려움 |
| chatml | 현 고정 Runtime에서 tools가 없는 prompt로 처리, 후보 제외 |
| tools XML로 호출 직렬화 통일 | 직접 API 5조건 통과, OpenCode 일부 도구 성공; 조건에 따라 JSON fence 출력 발생 |
| JSON code fence로 호출 직렬화 통일 | 직접 API 5조건 및 최소 OpenCode 도구 구성 통과 |

- JSON fence는 Runtime template의 명시적인 도구 호출 문법
- assistant의 구조화된 호출 이력을 같은 문법으로 렌더링하여 Runtime 자동 parser가 호출 경계를 인식
- 클라이언트에서 JSON content를 임의로 추출·실행하는 fallback 미사용
- tool_choice=none이면 JSON 모양 content가 있어도 tool_calls로 실행하지 않음

## 적용 및 되돌리기

```bash
make down
make up
make smoke
make tool-smoke
make opencode-smoke
```

- `make up`: template 파일 존재 확인, 읽기 전용 마운트 및 --chat-template-file 적용
- 기본 경로: `.env.example`, 개인 설정은 `.env`의 CHAT_TEMPLATE_FILE 값으로 변경 가능
- 원래 T001 template 복원: `.env`에 `CHAT_TEMPLATE_FILE=` 지정 후 down/up
- 되돌리기 시 직접 tool smoke 및 OpenCode 도구 검증 실패 재발 예상
- 모델·Runtime 재빌드 및 재다운로드 불필요
- template SHA256: `ce1a27271cbf39b880cd1a51ce84189e3448a5e911d83b334547169ae99910a7`
- 기반·라이선스: [template 출처](../../configs/llama/README.md)

## 직접 API 검증

```bash
make tool-smoke
# 별도 진단 서버에 적용하는 경우
python3 scripts/tool-calling-smoke.py --base-url http://127.0.0.1:18002/v1
```

| 검증 | 기대 결과 |
| --- | --- |
| auto | add 호출 1개, ID·함수명·JSON arguments 확인 |
| required | 같은 구조의 도구 호출 확인 |
| 이름 지정 | 지정한 add 함수 호출 확인 |
| stream | SSE delta.tool_calls 조립, ID·인자 및 tool_calls finish와 DONE 확인 |
| none | 구조화된 tool_calls 없음 |
| tool 결과 회신 | 실제 add 결과 5를 role=tool과 동일 tool_call_id로 회신, 반복 호출 없이 결과 반영 |

- 기본 서버 직접 API 실행 ID: `20260913T122613342895Z`, 5조건 통과
- 성공 시 종료 코드 0, 실패·누락·불완전 스트림은 1
- 요청·응답 및 결과: `.local/results/tool-calling/<UTC 시각>/`
- 단위 검사: content-only 가짜 호출 거부, 분할 SSE arguments 조립, DONE 누락·잘못된 함수 거부
- 검증 범위: 단일 간단한 add 함수, 복잡한 JSON schema·다중 동시 호출·일반적인 tool_choice 준수 전체 보장 제외

## OpenCode 재검증

- 기본 서버의 실행 ID: `20260913T122518925255Z`
- 결과: 모든 fixture 행동 조건 통과, OpenCode 및 harness 종료 코드 0
- 실제 실행: 실패 unittest → ls → 파일 read → grep → edit → 성공 unittest → git diff
- 변경 파일: calculator.py만 변경, `return a - b`에서 `return a + b`로 수정
- 검사기에서 작업 전후 전체 fixture 파일 해시 및 Git diff 확인
- GPU 샘플: 67개, 장치 전체 VRAM 8009–8322 MiB, GPU 사용률 10–99%
- 서버 관측: 같은 구간에서 12건 처리, CUDA 29/29 layer offload 유지
- 장치 전체 수치는 다른 프로세스 점유 포함, 모델 단독 메모리 또는 성능 벤치마크 아님

## 남은 제약

- 최초 5종 도구 구성은 실행 이력 누적으로 context 4096 도달, 도구 형식 문제 해결 뒤 드러난 별도 제약
- 현재 read·edit·bash 3종 사용, 탐색·검색은 실제 bash ls·grep로 수행
- temperature=0, 최대 10단계로 fixture 범위 제한
- 단계 제한 없이 실행하면 git diff 반복 또는 불필요한 stage/commit 시도 관측, stage/commit은 권한 거부
- 성공 실행의 마지막 응답은 OpenCode의 최대 단계 안내, 자연스러운 최종 요약 품질은 미해결
- 실제 작업 성공 판정은 모델의 완료 주장 대신 도구 이벤트·실패/성공 테스트·변경 파일로 수행
- 큰 저장소·장기 대화·범용 자율 Coding Agent 적합성은 별도 검증 필요
- T001 성능 수치는 내장 template 기준의 과거 측정으로 보존, 본 변경 후 값과 혼용 금지

## 관련 문서

- [ADR-003](../decisions/ADR-003-tool-calling-template.md)
- [OpenCode 운영](opencode.md)
- [API 계약](../specs/inference-api.md)
- [완료 작업](../tasks/completed/T002-opencode-agent-integration/README.md)
