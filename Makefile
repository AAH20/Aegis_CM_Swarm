PYTHON ?= python
DOCKER_COMPOSE ?= docker compose

.PHONY: up down build demo demo-online elevenlabs arena

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