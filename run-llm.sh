#!/usr/bin/env bash
# Runs a prompt from prompts/ against an OpenAI-compatible endpoint and writes
# the test files it returns.
#
# The model is the one configured for `make hybrid` - LLM_MODEL in .env - so
# that the LLM-only column and the hybrid column of the experiment use the same
# model, and the comparison is about the method rather than about the model.
#
#   bash run-llm.sh prompts/llm-from-spec.md
#   op run --env-file=.env.op -- bash run-llm.sh prompts/llm-from-spec.md
#
# The key is read from the environment only, never passed as an argument -
# arguments are visible in `ps` and in shell history.
set -euo pipefail

PROMPT="${1:?give me a prompt file}"
ENV_FILE="${ENV_FILE:-.env}"
# Where the generated files land. Point it elsewhere to compare two models
# without one overwriting the other's suite.
export TESTS_DIR="${TESTS_DIR:-tests_llm}"

if [ -f "$ENV_FILE" ]; then set -a; . "./$ENV_FILE"; set +a; fi

if [ -z "${PYNGUIN_OPENAI_API_KEY:-}${OPENAI_API_KEY:-}${LLM_API_KEY:-}" ]; then
  echo "no API key."
  echo "  op run --env-file=.env.op -- bash run-llm.sh $PROMPT"
  echo "or copy .env.op to $ENV_FILE and fill in the values."
  exit 1
fi

exec python3 - "$PROMPT" <<'PY'
import json, os, pathlib, re, sys, urllib.error, urllib.request

prompt_path = pathlib.Path(sys.argv[1])
name = prompt_path.stem

key = (os.environ.get("PYNGUIN_OPENAI_API_KEY")
       or os.environ.get("OPENAI_API_KEY")
       or os.environ.get("LLM_API_KEY"))
model = os.environ.get("LLM_MODEL") or "gpt-4o-mini"
base = (os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

text = prompt_path.read_text()
# Body of the prompt: everything after the front matter.
body = text.split("---\n", 2)[2] if text.startswith("---\n") else text

# A chat completion has no tools, so the inputs the prompt refers to travel
# with the request. That also enforces the "do not look at the answer"
# constraint by construction: the model sees these files and nothing else.
INPUTS = ["SPEC.md", "src/loyalty.py", "src/invoice.py"]
parts = [body.strip(), "", "Here are the files referred to above."]
for f in INPUTS:
    parts += ["", f"### {f}", "", "```", pathlib.Path(f).read_text().rstrip(), "```"]
message = "\n".join(parts)

req_body = {"model": model, "messages": [{"role": "user", "content": message}]}
req = urllib.request.Request(
    f"{base}/chat/completions",
    data=json.dumps(req_body).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
)

print(f"==> {name}  (model: {model}, endpoint: {base})")
try:
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
except urllib.error.HTTPError as e:
    detail = e.read().decode(errors="replace")[:500]
    sys.exit(f"    {e.code} {e.reason} from {base}\n    {detail}")
except urllib.error.URLError as e:
    sys.exit(f"    could not reach {base}: {e.reason}")

artifacts = pathlib.Path("artifacts")
artifacts.mkdir(exist_ok=True)
# The request goes into the record too, so the transcript shows exactly what
# the model was given. It holds no key - that travels in the header.
(artifacts / f"{name}.json").write_text(
    json.dumps({"request": req_body, "response": resp}, indent=2, ensure_ascii=False))

choice = resp["choices"][0]
answer = choice["message"]["content"]
if choice.get("finish_reason") == "length":
    sys.exit(f"    response truncated by the model's output limit; "
             f"raw reply in artifacts/{name}.json")

# The model returns each file in its own fence, tagged with the path.
FENCE = re.compile(r"^```(?:python)?[ \t]+(\S+)[ \t]*\n(.*?)^```", re.S | re.M)
out_dir = pathlib.Path(os.environ.get("TESTS_DIR", "tests_llm"))
written = {}
for path, code in FENCE.findall(answer):
    src = pathlib.Path(path)
    if src.suffix != ".py" or src.parent.name != "tests_llm":
        continue
    # The prompt names tests_llm/ so the model writes the imports and paths it
    # would write for real; TESTS_DIR decides where the file actually lands.
    p = out_dir / src.name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(code)
    written[src.name] = len(code.splitlines())

expected = {"test_loyalty.py", "test_invoice.py"}
missing = expected - written.keys()
if missing:
    sys.exit(f"    the reply did not contain {', '.join(sorted(missing))}; "
             f"raw reply in artifacts/{name}.json")

u = resp.get("usage", {}) or {}
rec = {"model": resp.get("model", model), "endpoint": base,
       "promptTokens": u.get("prompt_tokens"),
       "completionTokens": u.get("completion_tokens"),
       "testsDir": str(out_dir), "files": written}
(artifacts / f"{name}.usage.json").write_text(json.dumps(rec, indent=2))

for path, lines in sorted(written.items()):
    print(f"    {out_dir / path}: {lines} lines")
print(f"    prompt tokens: {rec['promptTokens']}, "
      f"completion tokens: {rec['completionTokens']}")
PY
