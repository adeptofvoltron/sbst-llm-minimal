---
model: from LLM_MODEL in .env - the same model make hybrid uses
inputs: "SPEC.md, src/loyalty.py, src/invoice.py (sent with the request)"
output: "tests_llm/test_loyalty.py, tests_llm/test_invoice.py"
---

Write unit tests that verify the code in `src/` implements the agreed
business rule.

The source of truth about the requirements is `SPEC.md`. The code is
`src/loyalty.py` and `src/invoice.py`. All three files are included below.

The most important rule: **derive the oracle from the specification, not from
the code.** If the code does something other than what `SPEC.md` says, the
test must assert the behaviour **required by the specification** - that is, it
must fail on the current code. Do not fit assertions to whatever the code
currently returns.

Technical requirements:

- pytest, files `tests_llm/test_loyalty.py` and `tests_llm/test_invoice.py`
- import the modules directly (`import loyalty`, `import invoice`) - the tests
  are run with `PYTHONPATH=src`
- every assertion about a business rule must reference the `SPEC.md` section
  it follows from, in a comment or in the test name

Answer with exactly two fenced code blocks, each tagged with its path, and
nothing else before the first block:

````
```python tests_llm/test_loyalty.py
<the whole file>
```

```python tests_llm/test_invoice.py
<the whole file>
```
````

After the second block, list the divergences you found between the code and
the specification: file, rule from the specification, what the code does.
