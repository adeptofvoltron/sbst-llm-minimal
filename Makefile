# Four commands. Each one takes seconds.
#
#   make setup      - environment (once)
#   make sbst       - generate tests by search (Pynguin)
#   make seeds      - the same, but with semantic seeds from an LLM
#   make hybrid     - search that calls an LLM when it stalls (needs .env)
#   make coverage   - measure what the generated files ACTUALLY cover
#   make report     - show what Pynguin REPORTS (not the same thing)
#   make fwpw       - Fails Without / Passes With validation
#   make clean      - tidy up
#
# Every target takes MODULE=loyalty or MODULE=invoice (invoice by default),
# plus BUDGET=<seconds> and SEED=<seed>.
#
# `hybrid` takes four more, so that runs with different models can be kept side
# by side and compared (docs/FINDINGS.md, points 11 and 12):
#
#   MODEL=gpt-4o          which model to call (empty = LLM_MODEL from .env)
#   OUT=tests_hybrid_4o   where the suite lands; REPORT=<name> for the statistics
#   SRC=src_spec          modules with SPEC.md in the docstring, so the
#                         specification reaches the prompt at all
#   ASSERT=LLM            let the model write the assertions instead of
#                         deriving them from the observed execution

PYNGUIN = PYNGUIN_DANGER_AWARE=1 .venv/bin/pynguin
BUDGET ?= 20
SEED   ?= 42
MODULE ?= invoice
TESTS  ?= tests_sbst

# For `make hybrid` only.
ENV_FILE  ?= .env
# Empty on purpose. A non-empty default would beat $(ENV_FILE)'s LLM_MODEL and
# make that variable dead - the exact trap docs/FINDINGS.md point 8 describes in
# Pynguin's own get_model_name(). Precedence: MODEL= on the command line, then
# LLM_MODEL from $(ENV_FILE), then the fallback below.
MODEL     ?=
MODEL_DEFAULT = gpt-4o-mini
PLATEAU   ?= 25
LLM_SHARE ?= 0.5
LLM_LIMIT ?= 5
# Where the hybrid suite lands, so runs with different models can live side
# by side the way tests_llm and tests_llm_mini do.
# gpt-5 rejects every temperature but 1.0 with
# `unsupported_value` - and Pynguin swallows the error, degrading the run to
# plain SBST without a word. docs/FINDINGS.md point 11.
TEMP      ?= 0.8
# src_spec/ holds the same modules with SPEC.md pasted into the docstring - the
# only channel through which the specification reaches Pynguin's prompts.
SRC       ?= src
ASSERT    ?= MUTATION_ANALYSIS
OUT       ?= tests_hybrid
REPORT    ?= hybrid

.PHONY: setup sbst seeds hybrid coverage report fwpw clean

setup:
	uv venv --python 3.12
	uv pip install -e '.[dev]'

sbst:
	rm -rf tests_sbst/test_$(MODULE).py
	$(PYNGUIN) --project-path src --output-path tests_sbst \
	  --module-name $(MODULE) --maximum-search-time $(BUDGET) --seed $(SEED) \
	  --report-dir report/sbst \
	  --output_variables TargetModule,Coverage,BranchCoverage

seeds:
	rm -rf tests_seeds/test_$(MODULE).py
	$(PYNGUIN) --project-path src --output-path tests_seeds \
	  --module-name $(MODULE) --maximum-search-time $(BUDGET) --seed $(SEED) \
	  --initial-population-seeding True --initial-population-data seeds \
	  --report-dir report/seeds \
	  --output_variables TargetModule,Coverage,BranchCoverage,FoundTestCases

# The hybrid from the article, but without a pipeline of our own: Pynguin 0.46
# ships this mechanism built in (docs/FINDINGS.md, point 5). Needs an
# OpenAI-compatible endpoint.
#
# --algorithm LLMOSA is load-bearing. Every --call-llm-* flag below lives in
# LLMOSAAlgorithm, and the default DYNAMOSA ignores all of them without a word:
# the run succeeds, writes the flags into pynguin-config.toml and produces a
# plain SBST suite. docs/FINDINGS.md point 9.
#
# Configuration comes from $(ENV_FILE) - template in .env.op. The key is passed
# through the environment only, because require_api_key() looks for it there
# anyway, and an --api_key flag would be visible in `ps` and in shell history.
hybrid:
	@mkdir -p $(OUT)
	@rm -f $(OUT)/test_$(MODULE).py
	@if [ -f "$(ENV_FILE)" ]; then set -a; . "./$(ENV_FILE)"; set +a; fi; \
	if [ -z "$$PYNGUIN_OPENAI_API_KEY$$OPENAI_API_KEY$$LLM_API_KEY" ]; then \
	  echo "no API key."; \
	  echo "  op run --env-file=.env.op -- make hybrid MODULE=$(MODULE)"; \
	  echo "or copy .env.op to $(ENV_FILE) and fill in the values."; \
	  exit 1; \
	fi; \
	model="$(MODEL)"; \
	[ -n "$$model" ] || model="$${LLM_MODEL:-$(MODEL_DEFAULT)}"; \
	echo "==> hybrid: $(MODULE), model $$model, budget $(BUDGET)s, plateau $(PLATEAU)"; \
	$(PYNGUIN) --project-path $(SRC) --output-path $(OUT) \
	  --module-name $(MODULE) --maximum-search-time $(BUDGET) --seed $(SEED) \
	  --algorithm LLMOSA \
	  --model-name "$$model" \
	  --temperature $(TEMP) \
	  --assertion_generation $(ASSERT) \
	  --call-llm-on-stall-detection True \
	  --call-llm-for-uncovered-targets True \
	  --hybrid-initial-population True \
	  --llm-test-case-percentage $(LLM_SHARE) \
	  --max-plateau-len $(PLATEAU) \
	  --max-llm-interventions $(LLM_LIMIT) \
	  --report-dir report/$(REPORT) \
	  --output_variables TargetModule,Coverage,BranchCoverage,TotalLLMCalls,\
TotalLLMInputTokens,TotalLLMOutputTokens,TotalCodelessLLMResponses,Assertions,\
TotalAssertionsReceivedFromLLM,TotalAssertionsAddedFromLLM,\
LLMTotalParsedStatements,LLMTotalStatements,TotalLTCs

coverage:
	@for dir in tests_sbst tests_seeds tests_llm tests_llm_mini \
	           tests_hybrid tests_hybrid_4o tests_hybrid_gpt5; do \
	  if [ -f "$$dir/test_$(MODULE).py" ]; then \
	    printf "\n=== %s ===\n" "$$dir"; \
	    PYTHONPATH=src .venv/bin/python -m pytest "$$dir/test_$(MODULE).py" \
	      --cov=$(MODULE) --cov-branch --cov-report=term -q 2>&1 \
	      | grep -E "$(MODULE).py|passed|failed" || true; \
	  fi; \
	done

# Coverage as reported by Pynguin during the search. NOT the same as the
# coverage of the generated file - see docs/FINDINGS.md, point 1.
report:
	@printf "\ncoverage REPORTED by Pynguin (during the search):\n"
	@for r in sbst seeds hybrid; do \
	  if [ -f report/$$r/statistics.csv ]; then \
	    printf "  %-8s %s\n" "$$r" "$$(tail -1 report/$$r/statistics.csv)"; \
	  fi; \
	done
	@printf "\nACTUAL coverage of the generated files (pytest-cov):\n"
	@$(MAKE) --no-print-directory coverage MODULE=$(MODULE) 2>/dev/null | grep -E "===|$(MODULE).py" | sed 's/^/  /'

# Tautological validation: a suite that correctly detects the defect does NOT
# pass on the current code, and passes once the patch is applied.
fwpw:
	@printf "\n=== before the patch (code with the defect) ===\n"
	@PYTHONPATH=src .venv/bin/python -m pytest $(TESTS)/test_loyalty.py -q 2>&1 | tail -2
	@git apply patches/fix_loyalty.patch
	@printf "\n=== after the patch (code matching SPEC.md) ===\n"
	@PYTHONPATH=src .venv/bin/python -m pytest $(TESTS)/test_loyalty.py -q 2>&1 | tail -3
	@git apply -R patches/fix_loyalty.patch
	@printf "\n(patch reverted)\n"

clean:
	rm -rf report .pytest_cache __pycache__ src/__pycache__ .coverage
