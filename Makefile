SHELL := /usr/bin/env bash

.SHELLFLAGS := -euo pipefail -c


.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync --all-extras
	@uv run pre-commit install

## Public target --------------------------------------------------------------
check:                     # 1st run; if anything fails we run a 2nd pass
	@$(MAKE) --no-print-directory _check \
	 || (echo '🔄 1st pass failed – trying once more …' >&2 ; \
	     $(MAKE) --no-print-directory _check)

## Private target (real work) -------------------------------------------------
_check:
	# stop on first error in each pass
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock
	@echo "🚀 Ruff lint (may auto-fix)"
	@uv run ruff check src tests
	@echo "🚀 pre-commit hooks (may auto-fix)"
	@uv run pre-commit run -a
	@echo "🚀 mypy static types"
	@uv run mypy
	@echo "🚀 deptry – unused / missing deps"
	@uv run deptry src

.PHONY: pbdiff
pbdiff: ## Copy git diff to clipboard
	 @git diff -- . ':(exclude)uv.lock' | pbcopy

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest -x --ff

.PHONY: record
record: ## Rerecord VCR cassettes
	@echo "🚀 Recording VCR cassettes (new episodes)"
	@uv run python -m pytest --record-mode=new_episodes

.PHONY: rerecord
rerecord: ## Rerecord VCR cassettes
	@echo "🚀 Rerecording VCR cassettes (all)"
	@uv run python -m pytest --record-mode=all

.PHONY: cov
cov: ## Generate HTML coverage report
	@echo "🚀 Generating HTML coverage report"
	@uv run python -m pytest --cov --record-mode=all --cov-config=pyproject.toml --cov-report=html
	@uv run coverage report --show-missing && uv run coverage html

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: build ## Publish a release to PyPI.
	@echo "🚀 Publishing."
	@uvx twine upload -r pypi dist/*

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
