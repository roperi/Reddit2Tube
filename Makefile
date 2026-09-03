SHELL := /bin/sh

UV ?= uv
UV_RUN := $(UV) run --locked
RUFF ?= ruff
PYTEST ?= pytest
PRE_COMMIT ?= pre-commit

.DEFAULT_GOAL := help

.PHONY: help install format format-check lint test coverage check install-hooks hooks-check

help: ## Show available development commands
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the project and development dependencies
	$(UV) sync --locked --dev

format: ## Format Python source files with Ruff
	$(UV_RUN) $(RUFF) format .

format-check: ## Check Python formatting without modifying files
	$(UV_RUN) $(RUFF) format --check .

lint: ## Run Ruff lint checks
	$(UV_RUN) $(RUFF) check .

test: ## Run the offline test suite
	$(UV_RUN) $(PYTEST) -q

coverage: ## Run tests with the configured coverage gate
	$(UV_RUN) $(PYTEST) --cov --cov-report=term-missing

check: format-check lint coverage ## Run the complete local quality gate

install-hooks: ## Install pre-commit and pre-push hooks
	$(UV_RUN) $(PRE_COMMIT) install --hook-type pre-commit
	$(UV_RUN) $(PRE_COMMIT) install --hook-type pre-push

hooks-check: ## Run both configured hook stages against the repository
	$(UV_RUN) $(PRE_COMMIT) run --all-files --hook-stage pre-commit
	$(UV_RUN) $(PRE_COMMIT) run --all-files --hook-stage pre-push
