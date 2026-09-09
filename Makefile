# Cztery komendy. Kazda trwa sekundy.
#
#   make setup     - srodowisko (raz)
#   make sbst      - wygeneruj testy przeszukiwaniem (Pynguin)
#   make ziarna    - to samo, ale z ziarnami semantycznymi od LLM-a
#   make pokrycie  - zmierz, co FAKTYCZNIE pokrywaja wygenerowane pliki
#   make fwpw      - walidacja Fails Without / Passes With
#   make czysto    - posprzataj
#
# Wszystkie cele przyjmuja MODUL=loyalty albo MODUL=invoice (domyslnie invoice)
# oraz BUDZET=<sekundy> i ZIARNO=<seed>.

PYNGUIN = PYNGUIN_DANGER_AWARE=1 .venv/bin/pynguin
BUDZET ?= 20
ZIARNO ?= 42
MODUL  ?= invoice
KATALOG ?= tests_sbst

.PHONY: setup sbst ziarna pokrycie fwpw czysto

setup:
	uv venv --python 3.12
	uv pip install -e '.[dev]'

sbst:
	rm -rf tests_sbst/test_$(MODUL).py
	$(PYNGUIN) --project-path src --output-path tests_sbst \
	  --module-name $(MODUL) --maximum-search-time $(BUDZET) --seed $(ZIARNO) \
	  --report-dir raport/sbst \
	  --output_variables TargetModule,Coverage,BranchCoverage

ziarna:
	rm -rf tests_ziarna/test_$(MODUL).py
	$(PYNGUIN) --project-path src --output-path tests_ziarna \
	  --module-name $(MODUL) --maximum-search-time $(BUDZET) --seed $(ZIARNO) \
	  --initial-population-seeding True --initial-population-data seeds \
	  --report-dir raport/ziarna \
	  --output_variables TargetModule,Coverage,BranchCoverage,FoundTestCases

pokrycie:
	@for katalog in tests_sbst tests_ziarna tests_llm tests_hybryda; do \
	  if [ -f "$$katalog/test_$(MODUL).py" ]; then \
	    printf "\n=== %s ===\n" "$$katalog"; \
	    PYTHONPATH=src .venv/bin/python -m pytest "$$katalog/test_$(MODUL).py" \
	      --cov=$(MODUL) --cov-branch --cov-report=term -q 2>&1 \
	      | grep -E "$(MODUL).py|passed|failed" || true; \
	  fi; \
	done

# Walidacja tautologiczna: suite, ktory poprawnie wykrywa defekt, NIE
# przechodzi na obecnym kodzie i przechodzi po nalozeniu patcha.
fwpw:
	@printf "\n=== przed patchem (kod z defektem) ===\n"
	@PYTHONPATH=src .venv/bin/python -m pytest $(KATALOG)/test_loyalty.py -q 2>&1 | tail -2
	@git apply patches/fix_loyalty.patch
	@printf "\n=== po patchu (kod zgodny ze SPEC.md) ===\n"
	@PYTHONPATH=src .venv/bin/python -m pytest $(KATALOG)/test_loyalty.py -q 2>&1 | tail -3
	@git apply -R patches/fix_loyalty.patch
	@printf "\n(patch cofniety)\n"

czysto:
	rm -rf raport .pytest_cache __pycache__ src/__pycache__ .coverage
