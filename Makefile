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
	$(flakehell) lint data_generator query_timer
	$(flakehell) lint batch_size_automator float_simulator tictrack
	#$(flakehell) lint tests

format: virtualenv-dev
	$(black) data_generator query_timer
	$(black) batch_size_automator float_simulator tictrack

test: virtualenv-dev
	$(pytest) -vvv tests

coverage: virtualenv-dev
	$(pytest) \
	    --cov=data_generator --cov=query_timer --cov=batch_size_automator --cov=float_simulator --cov=tictrack \
	    --cov-fail-under=95 --cov-branch --cov-report=term tests
