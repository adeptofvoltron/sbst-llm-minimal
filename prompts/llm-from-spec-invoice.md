---
model: from LLM_MODEL in .env, overridable in the environment
inputs: "SPEC.md, src/invoice.py (sent with the request)"
output: "tests_llm/test_invoice.py"
---

Write unit tests that verify the code in `src/invoice.py` implements the
agreed business rule.

The source of truth about the requirements is `SPEC.md`. The code is
`src/invoice.py`. Both files are included below.

The most important rule: **derive the oracle from the specification, not from
the code.** If the code does something other than what `SPEC.md` says, the
test must assert the behaviour **required by the specification** - that is, it
must fail on the current code. Do not fit assertions to whatever the code
currently returns.

Technical requirements:

- pytest, file `tests_llm/test_invoice.py`
- import the module directly (`import invoice`) - the tests are run with
  `PYTHONPATH=src`
- every assertion about a business rule must reference the `SPEC.md` section
  it follows from, in a comment or in the test name

Answer with exactly one fenced code block, tagged with its path, and nothing
else before the block:

````
```python tests_llm/test_invoice.py
<the whole file>
```
````

After the block, list the divergences you found between the code and the
specification: file, rule from the specification, what the code does.
