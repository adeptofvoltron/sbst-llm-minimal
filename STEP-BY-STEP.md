# Step by step

Eight commands. The longest one takes **3 seconds**. Zero API calls - every LLM
result is committed.

The "what to say" lines are a hint, not a script.

---

## Before you go on stage

```bash
git clone https://github.com/adeptofvoltron/sbst-llm-minimal
cd sbst-llm-minimal
make setup
```

Check that it works:

```bash
make sbst MODULE=loyalty && make fwpw
```

You should see `assert 172 == 171`. If you do, you are ready.
Finish with `make clean`.

---

## 1. The code (30 s)

```bash
cat src/loyalty.py
```

```python
def award_points(order_value_pln: float, lifetime_spend_pln: float) -> int:
    if order_value_pln < 0 or lifetime_spend_pln < 0:
        raise ValueError("amounts must not be negative")

    points = int(order_value_pln // 10)

    if lifetime_spend_pln > VIP_THRESHOLD_PLN:
        points = points * 2

    if points > POINTS_CAP:
        return POINTS_CAP
    return points
```

**What to say:** eight lines, no magic, passes review. And now the
specification.

```bash
sed -n '/Conversion rate/,/even one/p' SPEC.md
```

> A customer earns **1 point for every 10 PLN**. The result of the division is
> rounded using **banker's rounding**.

**What to say:** `//` truncates. That is not banker's rounding. The second
divergence: the specification says VIP means **at least** 5000, the code has
`>`. No exception is raised, the code is internally consistent - it just
computes something other than what was agreed.

---

## 2. SBST generates tests (3 s)

```bash
make sbst MODULE=loyalty
```

```bash
sed -n '5,12p' tests_sbst/test_loyalty.py
```

```python
def test_case_0():
    float_0 = 1716.363
    int_0 = module_0.award_points(float_0, float_0)
    assert int_0 == 171
```

**What to say:** `1716.363 / 10 = 171.6363`. The specification requires `172`.
The tool ran the function, saw `171` and wrote **that** down as the
expectation. It does not know the requirements - it only knows the code.

---

## 3. The punchline: we fix the code, the tests break (1 s)

```bash
make fwpw
```

```
=== before the patch (code with the defect) ===
3 passed in 0.01s

=== after the patch (code matching SPEC.md) ===
FAILED tests_sbst/test_loyalty.py::test_case_0 - assert 172 == 171
FAILED tests_sbst/test_loyalty.py::test_case_2 - assert 438 == 437
2 failed, 1 passed in 0.02s

(patch reverted)
```

**What to say:** `assert 172 == 171`. I fixed a bug in line with the
specification and got a red build. This suite is a regression barrier
protecting a bug.

This is not a failure of the tool - it is its premise. And this is the only way
to see it: apply the fix and check whether the tests change their mind. It is
called **Fails Without / Passes With**.

> The fix is one line: `round(order_value_pln / 10)`. In Python `round()`
> **is** banker's rounding - `round(2.5) == 2`, `round(3.5) == 4`.

---

## 4. The format gate (3 s)

```bash
sed -n '5p' src/invoice.py
```

```python
_PATTERN = re.compile(r"^FV/(\d{4})/(0[1-9]|1[0-2])/(\d{4})$")
```

```bash
make sbst MODULE=invoice
cat tests_sbst/test_invoice.py
```

The generated tests, in full:

```python
def test_case_0():
    str_0 = "s"
    with pytest.raises(ValueError):
        module_0.parse_invoice_id(str_0)
```

**What to say:** one test. A random string. An exception. All the logic behind
the gate - the year range, the zero sequence number, the returned dictionary -
untouched. A valid prefix is fifteen characters in a fixed order; random
sampling has no way of hitting that.

---

## 5. Semantic seeds - and the trap (3 s)

```bash
cat seeds/test_invoice.py
```

**What to say:** three cases an LLM would write after reading the
specification. We hand them to the search as its initial population. This is
CodaMosa's mechanism, available in Pynguin as a flag.

```bash
make seeds MODULE=invoice
make report MODULE=invoice
```

```
coverage REPORTED by Pynguin (during the search):
  sbst     "invoice","0.2222222222222222","0.2222222222222222"
  seeds    "invoice","0.8888888888888888","0.8888888888888888","3"

ACTUAL coverage of the generated files (pytest-cov):
  === tests_sbst ===
  src/invoice.py      14      8      6      1    35%
  === tests_seeds ===
  src/invoice.py      14      8      6      1    35%
  === tests_llm ===
  src/invoice.py      14      0      6      0   100%
```

**What to say:** top of the screen - the seeds raised coverage from 22% to 89%,
four times as much. Bottom of the screen - **both generated files are at 35%.**
The seeds covered the logic during the search and never made it into the
exported suite.

Had I taken the number from the report and put it on a slide, I would have been
telling a fairy tale. The moral: **measure the artifact, not the tool's
report.**

> Checked at a budget of 20 s and 60 s, with a raised timeout,
> `--seed-from-archive` and `--initial-population-mutations 0`. 35% every time.
> Details: `docs/FINDINGS.md`, point 1.

---

## 6. The LLM with the specification (1 min, no API)

The last row of the previous table: **100%**.

```bash
grep "^def test" tests_llm/test_loyalty.py | head -4
```

```python
def test_przelicznik_przyklady_ze_spec_sekcja_1(order_value_pln, oczekiwane):
def test_przelicznik_zaokraglenie_bankierskie_sekcja_1(order_value_pln, ...):
```

**What to say:** the test names are sentences about the requirements, with the
number of the specification section. Compare that with `test_case_0`.

> These tests come from a run of the original Polish prompt, so their names are
> in Polish; they are kept exactly as the model produced them. Regenerating
> with `bash run-llm.sh prompts/llm-from-spec.md` replaces them.

Now the same validation that exposed the SBST suite - this time on this suite:

```bash
make fwpw TESTS=tests_llm
```

```
=== before the patch (code with the defect) ===
16 failed, 28 passed in 0.10s

=== after the patch (code matching SPEC.md) ===
44 passed in 0.04s
```

**What to say:** exactly the opposite of SBST. Sixteen tests fail on the code
with the defects - **and that is the correct result**. Once the fix is applied,
all 44 are green.

That is the whole difference between these two suites: not the coverage, not
the number of tests, but **where the expectation came from**.

And now the second module, where it gets interesting:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests_llm/test_invoice.py -q
```

```
FAILED tests_llm/test_invoice.py::test_walidacja_cyfry_spoza_ascii_sekcja_2
1 failed, 49 passed
```

**What to say:** one test fails and it has nothing to do with rounding. The
code held **two** planted divergences. This one is the third.

---

## 7. The defect nobody planted (1 min)

```bash
PYTHONPATH=src .venv/bin/python
```

```python
>>> import invoice
>>> invoice.parse_invoice_id("FV/٢٠٢٦/09/0042")
{'year': 2026, 'month': 9, 'seq': 42}
```

**What to say:** this is the test that was failing. A year written in
Arabic-Indic digits passed validation.

```python
>>> import re
>>> re.match(r"\d{4}", "٢٠٢٦")
<re.Match object; span=(0, 4), match='٢٠٢٦'>
>>> int("٢٠٢٦")
2026
```

**What to say:** `\d` in Python matches Unicode digits by default, and `int()`
converts them. The code held **two** planted divergences - this is the third
and nobody put it there. It was found by the LLM that was given the
requirements. The search never touched it.

The month rejects such input, because `(0[1-9]|1[0-2])` requires literal ASCII
characters - so the defect only affects the year and the sequence number. All
the harder to notice.

The fix is a flag: `re.compile(..., re.ASCII)`.

---

## 8. Closing (30 s)

```bash
PYNGUIN_DANGER_AWARE=1 .venv/bin/pynguin --help \
  | grep -oE "\-\-call-llm-on-stall-detection|\-\-max-plateau-len|\-\-llm-url" | sort -u
```

```
--call-llm-on-stall-detection
--llm-url
--max-plateau-len
```

**What to say:** the hybrid from the article - an LLM called when the search
stalls - is **built into Pynguin as a flag**. You do not have to build it, you
have to switch it on and give it an OpenAI-compatible endpoint.

Wrapped in `make hybrid`. The only target in this repository that needs a key
and touches the network - which is why it is not part of the presentation
script:

```bash
cp .env.op .env          # fill in the key; .env is in .gitignore
make hybrid MODULE=invoice
```

Two traps along the way (`docs/FINDINGS.md` point 8): without `python-dotenv`
Pynguin ignores `.env` without a word, and `LLM_MODEL` from the environment
loses to the non-empty default `gpt-4o-mini`.

---

## Tidying up

```bash
make clean
git checkout -- src/
git status --short      # should be empty
```

---

## If something goes wrong

| Symptom | Cause |
|---|---|
| `Environment variable 'PYNGUIN_DANGER_AWARE' not set` | you are running Pynguin without `make`; set `PYNGUIN_DANGER_AWARE=1` - this also applies to `--help`, which prints abbreviated help without it |
| `Provided testcases are not used.` | `--initial-population-data` has to point at a **directory**, and the file inside it has to be named `test_<module>.py` |
| numbers different from the ones in this document | `BUDGET` or `SEED` changed; the search is stochastic |
| `make setup` does not work | no `uv`; use `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` |
