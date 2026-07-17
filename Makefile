.PHONY: lint typecheck test check run

lint:
	.venv/bin/ruff check .

typecheck:
	.venv/bin/mypy src

test:
	.venv/bin/pytest

check: lint typecheck test

run:
	.venv/bin/uvicorn consultant.main:app --app-dir src --reload
