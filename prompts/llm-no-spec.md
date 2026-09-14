---
model: from LLM_MODEL in .env, overridable in the environment
inputs: "src/invoice.py (sent with the request)"
output: "tests_llm/test_invoice.py"
---

Write unit tests that verify the code in `src/invoice.py` implements the
agreed business rule.

The code is `src/invoice.py`, included below.

Technical requirements:

- pytest, file `tests_llm/test_invoice.py`
- import the module directly (`import invoice`) - the tests are run with
  `PYTHONPATH=src`

Answer with exactly one fenced code block, tagged with its path, and nothing
else before the block:

````
```python tests_llm/test_invoice.py
<the whole file>
```
````

After the block, list the defects you found in the code: what the code does,
and why it is wrong.
