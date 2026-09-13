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

evidence:
	bash scripts/evidence.sh
