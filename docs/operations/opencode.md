---
status: 현재
owners: [LocalForge]
last_reviewed: 2026-09-13
---

# OpenCode 연동 및 검증

- 현재 결과: 설치·로컬 provider·일반 응답·SSE·실제 fixture E2E 통과
- 실행 범위: 4096 context, 최대 10단계의 작은 Python fixture
- 성공한 행동: 실패 테스트 확인·탐색·읽기·검색·수정·재테스트·diff
- 최종 자연어 요약은 최대 단계 안내로 대체되는 한계 존재, 범용 자율 Agent 검증 아님
- 최초 tool calling 실패의 원인과 수정 근거: [호환성 진단](tool-calling.md)

## 설치

- 전제: Linux x86_64 / WSL2, Node.js·npm·Docker·Git·Python 3
- 검증 버전: Node.js 24.20.0, OpenCode 1.18.30
- 버전·무결성: `configs/opencode/package-lock.json` 고정
- 로컬 설치: `.local/tools/opencode`, 호스트 전역 설치 없음
- 실행 환경: Python/Git 컨테이너, Python base image digest 고정, apt 패키지의 시점별 차이는 가능

```bash
make opencode-install
```

- 동작: npm ci, 버전 확인, `localforge/opencode-sandbox:1.18.30` 이미지 빌드
- 최초 인터넷 연결 필요, 모델 추가 다운로드 없음

## 설정

- 기본 예제: [opencode.json](../../configs/opencode/opencode.json)
- endpoint: `LOCALFORGE_BASE_URL`, 기본 `http://127.0.0.1:18000/v1`
- 기본 및 보조 모델: `localforge/localforge-baseline`
- 다른 별칭 사용 시 로컬 설정의 model·small_model·provider.localforge.models 키를 함께 변경
- `LOCALFORGE_OPENCODE_CONFIG`: 개인 설정 경로, 기본은 저장소 예제
- GPU layer·GGUF·CUDA 및 template 경로는 Agent에 전달하지 않음
- 인증: 현재 localhost API는 secret 불필요, 외부 provider 로그인 불필요
- localforge만 허용, 공유·자동 업데이트·외부 모델 목록 fetch 비활성화

```bash
mkdir -p .local
cp configs/opencode/opencode.json .local/opencode.json
export LOCALFORGE_OPENCODE_CONFIG="$PWD/.local/opencode.json"
export LOCALFORGE_BASE_URL=http://127.0.0.1:18000/v1
```

- `chat`: 도구 없는 일반 응답 검증용
- `localforge`: read·edit·bash를 사용하는 최소 Agent
- 모델 temperature capability와 Agent temperature=0 설정
- context 4096 및 output 512, 자동 compaction 비활성화
- 최대 10단계: 작은 fixture 검증용 한도, 더 큰 작업의 완료 보장 제외

## 재현 검증

전제: 호환 template을 적용한 T001 서버의 `make smoke`, `make tool-smoke` 통과.

```bash
make opencode-smoke
```

1. `/tmp/localforge-agent-*`에 별도 Git fixture 생성
2. harness에서 초기 실패 테스트 확인 및 파일 해시 저장
3. OpenCode CLI의 일반 응답 및 임시 localhost 서버의 SSE delta 검증
4. Agent가 수정 전 실패 테스트를 직접 실행하도록 요청
5. ls·read·grep·edit·재테스트·git diff 수행 확인
6. 실제 도구 이벤트·전후 테스트·파일 해시·diff로 성공 판정
7. 서버 로그와 0.2초 간격 GPU 샘플 저장, 임시 서버·컨테이너·샘플러 종료

- 결과: `.local/results/opencode/<UTC 시각>/summary.json` 및 인접 증거
- 성공 종료 코드: 0, 실제 도구·테스트·파일 변경 조건 미충족 시 1
- fixture는 조사용 보존, 필요 없을 때 해당 출력의 workspace만 제거
- 일반 응답 성공과 정확한 문구 일치는 분리, 후자는 prompt_exact_match로 기록
- OpenCode CLI 종료 코드만으로 성공 판정 금지
- 모델이 생성한 일반 JSON 텍스트를 임의로 실행하는 fallback 없음
- tests-before/after는 harness 결과, Agent 테스트 실행은 agent.jsonl의 bash 이벤트로 별도 확인
- 진단용 서버 관측 시 `LOCALFORGE_INFERENCE_CONTAINER` 지정 가능, 기본은 localforge-baseline

## 수동 실행

검증 결과의 실제 workspace 경로를 사용.

```bash
bash scripts/opencode.sh /tmp/localforge-agent-실제경로 \
  run --agent chat '파이썬 함수를 간단히 설명해줘'
bash scripts/opencode.sh /tmp/localforge-agent-실제경로 \
  run --agent localforge '실패 테스트를 먼저 실행하고 원인을 수정한 뒤 재테스트와 git diff를 확인해줘'
```

- 대화형 TUI: 실제 터미널에서 `bash scripts/opencode.sh /tmp/localforge-agent-실제경로`
- TUI 확인: 초기 화면·Chat / LocalForge baseline 선택 표시·키보드 입력·UI_OK 응답 수신 검증, 전체 메뉴 조작은 미검증
- TUI 실행 오류 failed to map segment 발생 시 /tmp tmpfs의 exec 옵션 확인, OpenTUI가 임시 공유 라이브러리 로딩에 사용
- 재현용 상세 prompt: scripts/opencode-smoke.py의 PROMPT
- 테스트 저장소는 별도 .git 디렉터리 요구

## 권한과 위험

- 컨테이너: 호스트와 같은 UID, capability 제거, privilege 증가 금지, 루트 파일시스템 읽기 전용
- 작업공간·OpenCode 상태 및 일시적 /tmp 쓰기 가능, binary·설정 읽기 전용
- /tmp는 OpenTUI 공유 라이브러리 로딩을 위해 exec 허용, nosuid 유지 및 컨테이너 종료 시 폐기
- 호스트 home·SSH·Git credential·Docker socket·모델 파일 마운트 없음
- 상태: `.local/opencode-container-state`, 호스트 기존 로그인과 분리
- bash 허용: ls·일부 cat·grep·unittest·git diff/status, stage·commit·외부 웹·subagent 기본 거부
- shell 권한은 완전한 보안 경계가 아님, 테스트 코드도 실행 코드이므로 신뢰한 fixture에만 적용
- host network 사용, 네트워크 egress 자체 차단 구성은 아님
- 임시 OpenCode 제어 서버는 loopback 전용, 동일 호스트 사용자 접근 가능
- secret·세션·원시 로그는 Git 제외, 종료된 컨테이너 자동 제거
- 중단된 smoke는 정확한 localforge-opencode-smoke-* 컨테이너 이름을 확인한 뒤 정리
- 모델의 최종 요약·지시 준수·장기 작업 안정성은 제한, [상세 결과](tool-calling.md) 참조

## 공식 기준

- [Local provider](https://opencode.ai/docs/providers/)
- [Agent 설정](https://opencode.ai/docs/agents/)
- [권한](https://opencode.ai/docs/permissions/)
- [CLI](https://opencode.ai/docs/cli/)
- [SSE 서버](https://opencode.ai/docs/server/)
