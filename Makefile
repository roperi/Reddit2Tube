SHELL := /bin/sh

PYTHON ?= python3
PIP := $(PYTHON) -m pip
RUFF ?= ruff
PYTEST ?= pytest
PRE_COMMIT ?= pre-commit

.DEFAULT_GOAL := help

.PHONY: help install format format-check lint test coverage check install-hooks hooks-check

help: ## Show available development commands
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the project and development dependencies
	$(PIP) install -e '.[dev]'

format: ## Format Python source files with Ruff
	$(RUFF) format .

format-check: ## Check Python formatting without modifying files
	$(RUFF) format --check .

lint: ## Run Ruff lint checks
	$(RUFF) check .

test: ## Run the offline test suite
	$(PYTEST) -q

coverage: ## Run tests with the configured coverage gate
	$(PYTEST) --cov --cov-report=term-missing

check: format-check lint coverage ## Run the complete local quality gate

install-hooks: ## Install pre-commit and pre-push hooks
	$(PRE_COMMIT) install --hook-type pre-commit
	$(PRE_COMMIT) install --hook-type pre-push

hooks-check: ## Run both configured hook stages against the repository
	$(PRE_COMMIT) run --all-files --hook-stage pre-commit
	$(PRE_COMMIT) run --all-files --hook-stage pre-push
