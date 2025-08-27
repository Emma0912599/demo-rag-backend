.PHONY: help install run test lint format precommit

install:
	uv pip install -e .[dev]
	pre-commit install

run:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check . --fix

format:
	black .

precommit:
	pre-commit run --all-files
