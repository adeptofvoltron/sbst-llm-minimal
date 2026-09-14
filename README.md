# SBST vs LLM vs hybrid - a minimal example

The same experiment as in
[ai-kielce-prezentacja](https://github.com/adeptofvoltron/ai-kielce-prezentacja),
boiled down to **forty lines of production code** and a tool that needs no
build step at all.

Why Python: **there is no SBST tool native to TypeScript.** Checked on npm -
the only hit for "sbst" is a REST client for EvoMaster, and `jsfuzz` was
abandoned in 2022. For JS/TS that leaves SynTest, which does not parse
TypeScript, so it needs `tsc`, module mapping and a transformation of its
output (seven workarounds, described in that other repository).

**Pynguin** for Python needs none of that. No build, no configuration. It is
also exactly the tool **CodaMosa** was built on - the hybrid cited in the
article.

```
search over one module:  3 seconds
the whole setup:         two commands
production code:         40 lines
```

## The result in one table

`make coverage MODULE=invoice` - actual coverage of the generated files,
measured with `pytest-cov`, not as reported by the tool:

| | tests | coverage of `invoice.py` | divergence from SPEC |
|---|---|---|---|
| SBST (Pynguin, 20 s) | 1 | **35%** | cemented in |
| SBST + semantic seeds | 4 | **35%** | cemented in |
| hybrid, `gpt-4o-mini` | 5 | **70%** | not detected |
| hybrid, `gpt-4o` | 6 | **100%** | not detected |
| hybrid, `gpt-5` | 5 | **100%** | not detected |
| hybrid + spec in the docstring, `gpt-4o` | 4 | 89% | **false positive** |
| LLM with the spec, `gpt-4o-mini` | 4 | **100%** | not detected |
| LLM with the spec, `claude-opus-5` | 50 | **100%** | **detected** |

The hybrid rows need a key and vary between runs. `gpt-4o` is a real gain on
coverage - 70% to 100%, and the first hybrid suite for `loyalty` at all - and
no gain at all in the last column, which is point 11.

The sixth row is worth the detour. Paste `SPEC.md` into the module docstring
and add `--assertion_generation LLM` and the model does write assertions from
the requirements: on `loyalty`, one of three seeds produced a single assertion
pinning **both** planted divergences. Pynguin then deleted 70-90% of what the
model returned, because the pass that runs afterwards drops every assertion
that fails - which is every assertion that detected anything. On `invoice`
what survived was a mangled `assert dict_0 is None` that fails on correct and
incorrect code alike. Point 12.

Note the bottom two rows: **same prompt, same specification, same code, 100%
coverage both times, and only one of them detects anything.** Coverage and
oracle are separate axes; the last column is the one that matters and no
percentage predicts it. Details in [`docs/FINDINGS.md`](docs/FINDINGS.md),
point 10.

Four things that follow from this, none of which we planned:

1. **Seeds raised the coverage Pynguin reports from 22.2% to 88.9%, and the
   coverage of the generated file by not a single point.** Measure the
   artifact, not the report.
2. **The LLM with the specification found a defect nobody planted**: `\d` in
   Python matches Unicode digits, so `FV/٢٠٢٦/09/0042` passed validation and
   `int()` politely returned `2026`.
3. **Pynguin deletes the assertions that find defects.** Not a metaphor:
   `__remove_non_holding_assertions` executes the suite and drops everything
   that does not pass, so an assertion derived from the specification and
   contradicting the code is removed by construction. Point 12.
4. **The hybrid from the article is a flag in Pynguin**, not a pipeline -
   `--call-llm-on-stall-detection`, `--max-plateau-len`, `--llm-url`. Set those
   flags alone and you get a run that succeeds, records them in its config and
   ignores every one of them: they only take effect under
   `--algorithm LLMOSA`, and the algorithm defaults to DYNAMOSA.

Details of each: [`docs/FINDINGS.md`](docs/FINDINGS.md).

---

## Want to present this?

[`STEP-BY-STEP.md`](STEP-BY-STEP.md) - eight commands, the longest one takes 3
seconds, zero API calls. Every command and every expected result was run
exactly as written down.

---

## Setup

```bash
git clone https://github.com/adeptofvoltron/sbst-llm-minimal
cd sbst-llm-minimal
make setup
```

`make setup` runs `uv venv --python 3.12` and `uv pip install -e '.[dev]'`.
Without `uv`:

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
```

Requires Python 3.10-3.14 (Pynguin 0.46 does not support 3.15+).

---

## Code that works and implements the wrong rule

`src/loyalty.py`, in full:

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

`SPEC.md` section 1 says two things differently:

- points are rounded using **banker's rounding** - and `//` truncates,
- VIP means a lifetime spend of **at least** 5000 PLN - and the code has `>`.

A Python detail: `round()` **is** banker's rounding (`round(2.5) == 2`,
`round(3.5) == 4`). The fix is one line - see `patches/fix_loyalty.patch`.

---

## Step 1: SBST generates tests from the behaviour of the code (3 s)

```bash
make sbst MODULE=loyalty
```

```python
def test_case_0():
    float_0 = 1716.363
    int_0 = module_0.award_points(float_0, float_0)
    assert int_0 == 171
```

`1716.363 / 10 = 171.6363`. The specification requires `172`. The code returns
`171` because it truncates - and the test pinned exactly that as the
expectation.

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests_sbst/test_loyalty.py -q
```

```
3 passed
```

Green - and it could not have been otherwise.

---

## Step 2: we fix the code, the tests break (1 s)

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

**`assert 172 == 171`** - one line that says everything. A fix that matches the
specification breaks the tests. The suite works as a regression barrier
protecting a bug.

This is not a failure of the tool. It is its premise: the code is the source of
truth about what should happen. This is called **tautological validation**
(Fails Without / Passes With) and it is the only way to tell "the test caught a
bug" apart from "the test cemented a bug".

---

## Step 3: the format gate (3 s)

`src/invoice.py` has one line that decides everything:

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

**One test. A random string. An exception.** All the logic behind the gate -
the year range, the zero sequence number, the returned dictionary - is
untouched.

```bash
make coverage MODULE=invoice
```

```
=== tests_sbst ===
src/invoice.py      14      8      6      1    35%
```

---

## Step 4: semantic seeds (3 s)

`seeds/test_invoice.py` holds three cases an LLM would write after reading
`SPEC.md` - handed to the search as its **initial population**. The mechanism
comes from CodaMosa and is available in Pynguin as a flag:

```bash
make seeds MODULE=invoice
```

Pynguin reports:

| | branch coverage (Pynguin's report) |
|---|---|
| without seeds | **22.2%** |
| with seeds | **88.9%** (`FoundTestCases: 3`) |

Four times as much, at the same random seed and the same budget.

**But that is not the whole truth** - and it is the most interesting thing in
this repository. See [`docs/FINDINGS.md`](docs/FINDINGS.md), point 1.

---

## Step 5: the LLM with the specification

The tests are committed, so this step needs no API key. The prompt is in
[`prompts/llm-from-spec.md`](prompts/llm-from-spec.md), and the full request
and reply are recorded in `artifacts/`.

```bash
make coverage MODULE=loyalty
make fwpw TESTS=tests_llm
```

To regenerate from scratch (needs a key):

```bash
# key from .env
bash run-llm.sh prompts/llm-from-spec.md

# or without the key ever touching disk
op run --env-file=.env.op -- bash run-llm.sh prompts/llm-from-spec.md
```

`run-llm.sh` uses the same configuration as `make hybrid` - `LLM_MODEL`,
`LLM_BASE_URL` and the key from `.env`. A plain chat completion has no tools,
so the script sends `SPEC.md` and both source files with the request and writes
the two files out of the reply; the model never sees the rest of the
repository.

`TESTS_DIR` picks where the suite lands, so two models can be compared side by
side. That is how `tests_llm_mini/` was produced, and comparing it with
`tests_llm/` turned out to be the sharpest result in the repository - see
[`docs/FINDINGS.md`](docs/FINDINGS.md), point 10:

```bash
TESTS_DIR=tests_llm_mini bash run-llm.sh prompts/llm-from-spec.md
```

> The committed `tests_llm/` predates this: it comes from a run of the original
> Polish prompt through Claude Code, which is why the generated test names are
> in Polish. Those files and their transcript
> (`artifacts/llm-from-spec.claude-code.jsonl`) are kept byte for byte as the
> model produced them. Regenerating with the command above replaces the tests
> and writes its own record next to it.

---

## All the commands

| Command | What it does | Time |
|---|---|---|
| `make setup` | environment | ~20 s |
| `make sbst MODULE=loyalty` | search | 3 s |
| `make seeds MODULE=invoice` | search with seeds | 3 s |
| `make hybrid MODULE=invoice` | search that calls an LLM when it stalls - **needs a key**, see `.env.op` | ~1 min |
| `make coverage MODULE=invoice` | actual coverage of the generated files | 1 s |
| `make report MODULE=invoice` | Pynguin's report **next to** the actual coverage | 2 s |
| `make fwpw` | Fails Without / Passes With validation | 1 s |
| `make clean` | tidy up | - |

Variables: `MODULE` (`loyalty` \| `invoice`), `BUDGET` (seconds),
`SEED` (random seed), `TESTS` (`tests_sbst` \| `tests_llm` \| `tests_llm_mini`
\| `tests_seeds` \| `tests_hybrid`).
For `hybrid` additionally: `PLATEAU` (how many iterations without progress
before the LLM is called), `LLM_SHARE`, `LLM_LIMIT`, `ENV_FILE`.

Everything except `make hybrid` runs **without an API key** and without network
access. `make hybrid` is the only target that needs an OpenAI-compatible
endpoint - configured in `.env` (template: `.env.op`; `.env` is in
`.gitignore`).

---

## What next

- [`docs/FINDINGS.md`](docs/FINDINGS.md) - what came out, including Pynguin's
  measurement trap and **the defect nobody planted**: `\d` in Python matches
  Unicode digits, so `FV/٢٠٢٦/09/0042` passed validation
- [`SPEC.md`](SPEC.md) - the requirements, i.e. the oracle
- the full version of the experiment, with mutation testing, five LLM variants
  and a four-stage hybrid:
  [ai-kielce-prezentacja](https://github.com/adeptofvoltron/ai-kielce-prezentacja)
