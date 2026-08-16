PYTHON ?= python3
DOCKER_COMPOSE ?= docker compose

.PHONY: up down build demo demo-online elevenlabs arena test identity-demo

up:
	$(DOCKER_COMPOSE) up --build

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

demo:
	$(PYTHON) demo.py

demo-online:
	AEGIS_OFFLINE=0 $(PYTHON) demo.py

elevenlabs:
	$(PYTHON) scripts/elevenlabs_demo.py

arena:
	$(PYTHON) -m uvicorn arena.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m unittest discover -s tests -v

identity-demo:
	@mkdir -p artifacts
	$(PYTHON) -m aegis.cli run \
		--intent examples/identity-intrusion/intent.json \
		--events examples/identity-intrusion/events.json \
		--dependencies examples/identity-intrusion/dependencies.json \
		--target build-runner-01 \
		--output artifacts/identity-intrusion-result.json
