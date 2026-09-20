---
status: 현재
owners: [LocalForge]
last_reviewed: 2026-09-20
---

# 한국어·코딩 응답 품질 평가

- 목적: 고정된 한국어 4건·코딩 4건의 응답과 문자 혼입 후보 기록
- 전제: 기존 baseline 서버 실행, Docker 접근, `.env.example` 및 `.env`가 실제 서버 구성과 일치
- 평가 세트: [korean-coding-v1.json](../../evals/korean-coding-v1.json)
- 실행 코드: [quality-eval.py](../../scripts/quality-eval.py), Python 표준 라이브러리 사용
- 생성된 코드 실행 없음, 정확성·지시 준수·자연스러움은 수동 판정

## 실행과 비교

```bash
make quality-eval
# 기본 출력: .local/results/quality/<UTC 시각>-<고유 ID>.json
bash scripts/quality-eval.sh --output .local/results/quality/run-a.json
bash scripts/quality-eval.sh --output .local/results/quality/run-b.json
bash scripts/quality-eval.sh --compare \
  .local/results/quality/run-a.json .local/results/quality/run-b.json
```

- 같은 출력 파일이 있으면 덮어쓰기 거부
- 요청 조건: temperature=0, seed=42, max_tokens=768, 동시성 1, 사례마다 독립 대화
- `--max-tokens`로 상한 변경 가능, 조건이 다른 결과 간 비교는 거부
- 실패한 요청도 기록하고 남은 사례 실행. 빈 응답·API 오류·`finish_reason != stop`은 불완전 결과 처리
- 종료 코드 0: 전체 응답 수집 완료, 모델 품질 합격 의미 아님
- 종료 코드 1: 불완전 수집·구성 불일치·비교 거부·입출력 오류
- 서버·모델 검증 단계에서 실패하면 평가 시작 전 종료, 결과 파일 미생성
- 결과 및 고정 프롬프트 응답은 Git 제외 `.local/results/`에 보관

## 기록 조건과 비교 제한

- 모델: 설정의 repository·revision·SHA256과 실제 마운트된 GGUF SHA256 대조
- Runtime: 선언한 전체 commit과 서버 build의 짧은 commit 대조, 실제 컨테이너 image ID 기록
- 서버: 컨테이너 실행 인자의 모델·context·GPU layers·parallel, GPU 장치와 포트 설정 대조
- Template: 서버가 제공한 실제 template SHA256 기록, 파일 override 사용 시 파일 내용·마운트 대조
- 고정 Runtime이 `/props`에서 생략하는 마지막 LF 1개 차이만 허용, 파일 원본 SHA256도 별도 기록
- 내장 template: `template_source=builtin`, 서버 제공 template의 SHA256 기록. null로 처리하지 않음
- 나머지 조건: 서버 generation 기본값, 평가 세트 내용 SHA256·버전·사례 ID, 판정 규칙·Unicode 버전, 요청 조건
- 전체 조건의 fingerprint가 다르거나 결과가 불완전하면 비교 거부
- 비교 출력: 사례별 응답 변화 여부와 혼입 후보 문자 수의 전후 차이. 품질 향상·정답 여부 자동 판정 없음
- 고정 seed·temperature도 GPU 실행의 완전한 결정성을 보장하지 않음. 동일 조건 반복 관찰 용도
- 실행 중 모델 파일·template·서버 재기동·설정 변경 금지. 시작 시점 검증이며 실행 중 변경 감시는 미지원
- Runtime 전체 commit은 선언값이며 실제 build가 제공하는 짧은 commit과 대조한 수준. image ID를 함께 보존

## 자동 수치 해석

| 필드 | 의미 |
| --- | --- |
| `hangul_letters` | 코드 제외 산문의 한글 문자 수, NFC 정규화 적용 |
| `latin_letters` | Latin 문자 수, 영문 기술 용어와 외국어 문장을 자동 구분하지 않음 |
| `other_letters` | 한글·Latin 이외 Unicode 문자 범주 L의 수, 한자·가나 등 혼입 후보 |
| `other_letter_ratio` | 기타 문자 / 집계 문자 전체, 분모가 0이면 null |
| `other_characters` | 혼입 후보 문자별 빈도 |
| `status` | 후보 없음·수동 검토 필요·판정 불가 상태 |

- fenced code와 inline code 제외. 닫히지 않은 fence 이후도 코드로 취급
- 숫자·구두점·공백·기호·emoji·결합 부호는 집계 제외
- `no_candidate_detected`: 기타 문자 0이며 한글 존재. 한국어 품질 합격 의미 아님
- `needs_manual_review`: 기타 문자 존재 또는 집계 문자 중 한글 없음
- `not_assessable`: 코드만 있거나 집계 문자 없음. 자동 합격으로 취급 금지
- 한자 고유명사 등 정상 사용도 후보로 집계 가능. Cyrillic 등의 다른 문자는 후보에 포함
- 영어 혼입의 자연스러움, 들여쓰기 코드·HTML 등 Markdown 변형, 문맥상 허용되는 외국어는 수동 확인

## 수동 판정

1. 각 사례의 `response`와 `manual.rubric` 대조
2. 정확성·요청 형식 준수·자연스러움을 사례별로 기록
3. 원본 결과 보존, 같은 이름의 별도 `.manual.md`에 사례 ID·pass/fail/unverified·근거 기록
4. 자동 수치와 수동 판정을 합친 총점 또는 모델 전반의 합격 주장 금지

- 최초 결과의 `manual.status=pending`, 자동 채점 대상과 명시적으로 구분
- 8건은 작은 진단 세트이며 대표성·품질 우위·회귀율 추정 근거로 부족
- 세트 수정 시 version 변경 권장, 내용 해시가 달라지면 기존 결과와 직접 비교 불가

## 검증

```bash
make test
python3 -m py_compile scripts/quality-eval.py
bash -n scripts/quality-eval.sh
```

- 단위 테스트: 문자 범주·code 제외·빈 산문·응답 오류 후 지속·잘림·조건 불일치·파일 보존
- 실제 baseline 수집과 기존 smoke 회귀는 로컬 수동 실행, GPU CI 실행은 범위 밖
- 작업 및 최초 실행 근거: [T003](../tasks/completed/T003-korean-coding-quality-eval.md)
