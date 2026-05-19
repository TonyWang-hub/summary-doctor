# summary-doctor — developer Makefile
#
# Usage:
#   make test              # run the test suite under the mock backend
#   make demo              # run summary-doctor against demos/01-reversal-en (mock)
#   make self-audit        # run summary-doctor on its own README (claude-cli haiku)
#   make self-audit-mock   # same, but mock backend (CI-friendly, no auth needed)
#   make self-audit-opus   # same, but claude-cli opus (slow, more accurate)
#   make clean             # remove build artefacts and caches

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

# Where to write timestamped self-audit reports when using the real backend.
# Mock runs stay in /tmp/ because they are smoke-tests, not artefacts worth
# keeping across runs. See docs/SELF-AUDIT.md.
SELF_AUDIT_DIR := eval/self-audit
SELF_AUDIT_TS   = $(shell date +%Y%m%d-%H%M%S)

.PHONY: help test demo self-audit self-audit-mock self-audit-opus clean install-dev _self-audit-prep _self-audit-check-cli

help:
	@echo "Targets:"
	@echo "  install-dev       Install the package in editable mode with dev extras"
	@echo "  test              Run pytest"
	@echo "  demo              Run summary-doctor on demos/01-reversal-en (mock backend)"
	@echo "  self-audit        Run summary-doctor on its own README (claude-cli, haiku)"
	@echo "  self-audit-mock   Run summary-doctor on its own README (mock backend, CI-safe)"
	@echo "  self-audit-opus   Run summary-doctor on its own README (claude-cli, opus)"
	@echo "  clean             Remove build artefacts and caches"

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

# --- self-audit ------------------------------------------------------------
#
# self-audit treats README.md as the "summary under test" and the concat of
# docs/SPEC.md + docs/ROADMAP.md as the "source". This is a stretch of the
# tool's intended use case — see docs/SELF-AUDIT.md for why a 60%-ish
# divergence on the mock target is *expected*, not a bug.

_self-audit-prep:
	@cat docs/SPEC.md docs/ROADMAP.md > /tmp/sd-self-source.txt

_self-audit-check-cli:
	@command -v claude >/dev/null 2>&1 || { \
	    echo "ERROR: 'claude' CLI not found in PATH."; \
	    echo "       The default self-audit target uses the claude-cli backend"; \
	    echo "       so it can reuse your Claude Code subscription auth."; \
	    echo "       Options:"; \
	    echo "         - install Claude Code, run 'claude --version' to verify, retry"; \
	    echo "         - or run 'make self-audit-mock' for the heuristic mock run"; \
	    echo "       Details: docs/SELF-AUDIT.md (section 'How to run')"; \
	    exit 1; \
	}

self-audit-mock: _self-audit-prep
	@echo "Running self-audit (mock backend): README vs SPEC + ROADMAP..."
	@PYTHONPATH=src $(PYTHON) -m summary_doctor README.md \
	    --original /tmp/sd-self-source.txt \
	    --lang en --mock \
	    --out /tmp/sd-self-audit-mock.md
	@rm -f /tmp/sd-self-source.txt
	@echo "Self-audit report: /tmp/sd-self-audit-mock.md"
	@echo "Note: mock divergence on README is a known artefact — see docs/SELF-AUDIT.md."

self-audit: _self-audit-check-cli _self-audit-prep
	@mkdir -p $(SELF_AUDIT_DIR)
	@echo "Running self-audit (claude-cli, haiku): README vs SPEC + ROADMAP..."
	@PYTHONPATH=src $(PYTHON) -m summary_doctor README.md \
	    --original /tmp/sd-self-source.txt \
	    --lang en \
	    --backend claude-cli --model haiku \
	    --out $(SELF_AUDIT_DIR)/$(SELF_AUDIT_TS)-haiku.md
	@rm -f /tmp/sd-self-source.txt
	@echo "Self-audit report: $(SELF_AUDIT_DIR)/$(SELF_AUDIT_TS)-haiku.md"

self-audit-opus: _self-audit-check-cli _self-audit-prep
	@mkdir -p $(SELF_AUDIT_DIR)
	@echo "Running self-audit (claude-cli, opus): README vs SPEC + ROADMAP..."
	@echo "Note: opus runs are slower; expect minutes, not seconds."
	@PYTHONPATH=src $(PYTHON) -m summary_doctor README.md \
	    --original /tmp/sd-self-source.txt \
	    --lang en \
	    --backend claude-cli --model opus \
	    --out $(SELF_AUDIT_DIR)/$(SELF_AUDIT_TS)-opus.md
	@rm -f /tmp/sd-self-source.txt
	@echo "Self-audit report: $(SELF_AUDIT_DIR)/$(SELF_AUDIT_TS)-opus.md"

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
