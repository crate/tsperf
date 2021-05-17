# =============
# Configuration
# =============

$(eval venv         := .venv)
$(eval pip          := $(venv)/bin/pip)
$(eval python       := $(venv)/bin/python)
$(eval pytest       := $(venv)/bin/pytest)
$(eval flakehell    := $(venv)/bin/flakehell)
$(eval black        := $(venv)/bin/black)

$(eval tsdg         := $(venv)/bin/tsdg)


# =====
# Setup
# =====

# Setup Python virtualenv
setup-virtualenv:
	@test -e $(python) || python3 -m venv $(venv)

# Install requirements for development.
virtualenv-dev: setup-virtualenv
	@test -e $(tsdg) || $(pip) install --editable=.[testing]


# ====
# Main
# ====

lint: virtualenv-dev
	$(flakehell) lint tsdg tsqt tests

format: virtualenv-dev
	$(black) tsdg tsqt tests

test: virtualenv-dev
	$(pytest) -vvv tests

coverage: virtualenv-dev
	$(pytest) --cov=tsdg --cov=tsqt --cov-fail-under=95 --cov-branch --cov-report=term tests
