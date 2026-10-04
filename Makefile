# Social Insights - Development Makefile
# All commands use the project-local venv. Nothing is ever installed globally.

PYTHON = .venv/Scripts/python.exe
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest
RUFF = $(PYTHON) -m ruff
UVICORN = $(PYTHON) -m uvicorn

.PHONY: setup test lint format run smoke clean

## setup: Create venv and install all dependencies
setup:
	C:/Python312/python.exe -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "Setup complete. Activate with: .venv\\Scripts\\activate"

## test: Run the full test suite
test:
	$(PYTEST) -v --tb=short

## test-cov: Run tests with coverage
test-cov:
	$(PYTEST) -v --cov=backend/app --cov-report=term-missing --tb=short

## lint: Run linter checks
lint:
	$(RUFF) check backend/
	$(RUFF) format --check backend/

## format: Auto-format code
format:
	$(RUFF) format backend/
	$(RUFF) check --fix backend/

## run: Start the backend dev server
run:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

## smoke: Run smoke test against local server
smoke:
	powershell -ExecutionPolicy Bypass -File scripts/smoke_test.ps1 http://localhost:8000

## clean: Remove generated files
clean:
	@if exist .venv rmdir /s /q .venv
	@if exist social_insights.db del social_insights.db
	@if exist .cache rmdir /s /q .cache
	@echo "Cleaned"
