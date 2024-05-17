# =============
# Configuration
# =============

$(eval venv         := .venv)
$(eval pip          := $(venv)/bin/pip)
$(eval python       := $(venv)/bin/python)
$(eval pytest       := $(venv)/bin/pytest)
$(eval flakehell    := $(venv)/bin/flakehell)
$(eval black        := $(venv)/bin/black)
$(eval isort        := $(venv)/bin/isort)

$(eval tsperf       := $(venv)/bin/tsperf)


# =====
# Setup
# =====

# Setup Python virtualenv
setup-virtualenv:
	@test -e $(python) || python3 -m venv $(venv)

# Install requirements for development.
virtualenv-dev: setup-virtualenv
	@test -e $(tsperf) || $(pip) install --editable='.[testing]'


# ====
# Main
# ====

lint: virtualenv-dev
	$(flakehell) lint tsperf tests

format: virtualenv-dev
	$(black) tsperf tests
	$(isort) tsperf tests

test: virtualenv-dev
	$(pytest) -vvv tests

coverage: virtualenv-dev
	$(pytest) --cov=tsperf --cov-fail-under=80 --cov-branch --cov-report=term tests
