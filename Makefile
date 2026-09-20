.PHONY: preflight build model up down logs smoke test
preflight:
	bash scripts/preflight.sh
build:
	bash scripts/build.sh
model:
	bash scripts/download.sh
up:
	bash scripts/server.sh up
down:
	bash scripts/server.sh down
logs:
	bash scripts/server.sh logs
smoke:
	bash scripts/smoke.sh
test:
	python3 -m unittest discover -s tests -v

.PHONY: quality-eval
quality-eval:
	bash scripts/quality-eval.sh

evidence:
	bash scripts/evidence.sh

.PHONY: opencode-install opencode-smoke
opencode-install:
	bash scripts/opencode-install.sh
opencode-smoke:
	python3 scripts/opencode-smoke.py

.PHONY: tool-smoke
tool-smoke:
	bash scripts/tool-calling-smoke.sh
