# Qwen2.5-Coder 도구 호환 template

- 대상: 고정 Qwen2.5-Coder-7B-Instruct Q4_K_M GGUF
- 기반: llama.cpp `56b9eb280a67796379d8625729fb03d72c70789d`의 Qwen2.5 template
- 실제 upstream commit: `.env.example`의 `LLAMA_REV` 참조
- 파일: `qwen25-tools.jinja`
- 변경: 호출 예제의 이중 중괄호 제거, 호출 지시와 assistant tool-call 직렬화를 JSON code fence로 일치
- JSON code fence는 이 template의 명시적인 도구 호출 형식, 일반 content를 클라이언트에서 재해석하는 fallback 아님
- 도구가 없는 대화 분기 및 tool 결과 직렬화는 upstream 형식 유지
- 모델·Runtime 업데이트 시 재사용을 가정하지 않고 `make tool-smoke` 재검증 필수
- 라이선스: [upstream MIT](UPSTREAM-LICENSE), 변경한 template에도 동일 조건 적용
- 근거: [upstream template](https://github.com/ggml-org/llama.cpp/blob/56b9eb280a67796379d8625729fb03d72c70789d/models/templates/Qwen-Qwen2.5-7B-Instruct.jinja)
