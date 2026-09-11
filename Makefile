# Cztery komendy. Kazda trwa sekundy.
#
#   make setup     - srodowisko (raz)
#   make sbst      - wygeneruj testy przeszukiwaniem (Pynguin)
#   make ziarna    - to samo, ale z ziarnami semantycznymi od LLM-a
#   make hybryda   - przeszukiwanie wolajace LLM, gdy staje (wymaga .env)
#   make pokrycie  - zmierz, co FAKTYCZNIE pokrywaja wygenerowane pliki
#   make raport    - pokaz, co RAPORTUJE Pynguin (to nie to samo)
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

# Tylko dla `make hybryda`.
PLIK_ENV   ?= .env
MODEL_LLM  ?= gpt-4o-mini
PLATO      ?= 25
UDZIAL_LLM ?= 0.5
LIMIT_LLM  ?= 5

.PHONY: setup sbst ziarna hybryda pokrycie raport fwpw czysto

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

# Hybryda z artykulu, ale bez wlasnego pipeline'u: Pynguin 0.46 ma ten mechanizm
# wbudowany (docs/USTALENIA.md punkt 5). Wymaga endpointu zgodnego z OpenAI.
#
# Konfiguracja idzie z $(PLIK_ENV) - wzor w .env.op. Klucz przekazujemy wylacznie
# przez srodowisko, bo require_api_key() i tak go tam szuka, a flaga --api_key
# byla by widoczna w `ps` i w historii powloki.
hybryda:
	@mkdir -p tests_hybryda
	@rm -f tests_hybryda/test_$(MODUL).py
	@if [ -f "$(PLIK_ENV)" ]; then set -a; . "./$(PLIK_ENV)"; set +a; fi; \
	if [ -z "$$PYNGUIN_OPENAI_API_KEY$$OPENAI_API_KEY$$LLM_API_KEY" ]; then \
	  echo "brak klucza do API."; \
	  echo "  op run --env-file=.env.op -- make hybryda MODUL=$(MODUL)"; \
	  echo "albo skopiuj .env.op do $(PLIK_ENV) i wstaw wartosci."; \
	  exit 1; \
	fi; \
	model="$${LLM_MODEL:-$(MODEL_LLM)}"; \
	echo "==> hybryda: $(MODUL), model $$model, budzet $(BUDZET)s, plateau $(PLATO)"; \
	$(PYNGUIN) --project-path src --output-path tests_hybryda \
	  --module-name $(MODUL) --maximum-search-time $(BUDZET) --seed $(ZIARNO) \
	  --model-name "$$model" \
	  --call-llm-on-stall-detection True \
	  --call-llm-for-uncovered-targets True \
	  --hybrid-initial-population True \
	  --llm-test-case-percentage $(UDZIAL_LLM) \
	  --max-plateau-len $(PLATO) \
	  --max-llm-interventions $(LIMIT_LLM) \
	  --report-dir raport/hybryda \
	  --output_variables TargetModule,Coverage,BranchCoverage

pokrycie:
	@for katalog in tests_sbst tests_ziarna tests_llm tests_hybryda; do \
	  if [ -f "$$katalog/test_$(MODUL).py" ]; then \
	    printf "\n=== %s ===\n" "$$katalog"; \
	    PYTHONPATH=src .venv/bin/python -m pytest "$$katalog/test_$(MODUL).py" \
	      --cov=$(MODUL) --cov-branch --cov-report=term -q 2>&1 \
	      | grep -E "$(MODUL).py|passed|failed" || true; \
	  fi; \
	done

# Pokrycie zgloszone przez Pynguina w trakcie przeszukiwania. NIE jest
# tozsame z pokryciem wygenerowanego pliku - patrz docs/USTALENIA.md, punkt 1.
raport:
	@printf "\npokrycie RAPORTOWANE przez Pynguina (w trakcie przeszukiwania):\n"
	@for w in sbst ziarna hybryda; do \
	  if [ -f raport/$$w/statistics.csv ]; then \
	    printf "  %-8s %s\n" "$$w" "$$(tail -1 raport/$$w/statistics.csv)"; \
	  fi; \
	done
	@printf "\npokrycie FAKTYCZNE wygenerowanych plikow (pytest-cov):\n"
	@$(MAKE) --no-print-directory pokrycie MODUL=$(MODUL) 2>/dev/null | grep -E "===|$(MODUL).py" | sed 's/^/  /'

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
