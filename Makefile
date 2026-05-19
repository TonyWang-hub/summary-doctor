# summary-doctor — developer Makefile
#
# Usage:
#   make test         # run the test suite under the mock backend
#   make demo         # run summary-doctor against demos/01-reversal-en using the mock backend
#   make self-audit   # placeholder, will run the tool on its own README in a future release
#   make clean        # remove build artefacts and caches

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help test demo self-audit clean install-dev

help:
	@echo "Targets:"
	@echo "  install-dev  Install the package in editable mode with dev extras"
	@echo "  test         Run pytest"
	@echo "  demo         Run summary-doctor on demos/01-reversal-en (mock backend)"
	@echo "  self-audit   Run summary-doctor on its own README (mock backend)"
	@echo "  clean        Remove build artefacts and caches"

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install pytest
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -v

demo:
	summary-doctor run \
	    --summary demos/01-reversal-en/summary.txt \
	    --source  demos/01-reversal-en/source.txt \
	    --backend mock

self-audit:
	@echo "Running self-audit: README claims vs SPEC + ROADMAP..."
	@cat docs/SPEC.md docs/ROADMAP.md > /tmp/sd-self-source.txt
	@PYTHONPATH=src $(PYTHON) -m summary_doctor README.md \
	    --original /tmp/sd-self-source.txt \
	    --lang en --mock \
	    --out /tmp/sd-self-audit.md
	@echo "Self-audit report: /tmp/sd-self-audit.md"
	@rm -f /tmp/sd-self-source.txt

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
