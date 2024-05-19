# Development Sandbox

## Setup
```shell
git clone https://github.com/crate/tsperf.git
cd tsperf
python3 -m venv .venv
source .venv/bin/activate
```

## Tests
Invoke linters and software tests.
```shell
source .venv/bin/activate
poe check
```

Run individual tests.
```shell
pytest -k test_calculate
```

Run code formatter.
```shell
poe format
```
