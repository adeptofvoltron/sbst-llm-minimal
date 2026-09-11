#!/usr/bin/env bash
# Runs a prompt from prompts/ through claude -p and saves the transcript.
set -euo pipefail
PROMPT="${1:?give me a prompt file}"
NAME="$(basename "$PROMPT" .md)"
MODEL="$(sed -n 's/^model: *//p' "$PROMPT" | head -1)"
EFFORT="$(sed -n 's/^effort: *//p' "$PROMPT" | head -1)"
BODY="$(awk 'seen==2 {print} /^---$/ {seen++}' "$PROMPT")"
mkdir -p artifacts
echo "==> $NAME  (model: $MODEL, effort: $EFFORT)"
printf '%s' "$BODY" | claude -p --model "$MODEL" --effort "$EFFORT" \
  --permission-mode bypassPermissions --output-format stream-json --verbose \
  > "artifacts/${NAME}.jsonl"
python3 - "$NAME" "$MODEL" "$EFFORT" <<'PY'
import json, sys
name, model, effort = sys.argv[1:4]
res, tools = {}, 0
for line in open(f"artifacts/{name}.jsonl"):
    line = line.strip()
    if not line: continue
    try: e = json.loads(line)
    except json.JSONDecodeError: continue
    if e.get("type") == "result": res = e
    for b in (e.get("message", {}) or {}).get("content", []) or []:
        if isinstance(b, dict) and b.get("type") == "tool_use": tools += 1
u = res.get("usage", {}) or {}
# The model comes from the prompt's front matter, not from modelUsage - that
# one can also list helper models, which makes the report misleading.
rec = {"model": model, "effort": effort, "turns": res.get("num_turns"),
       "costUSD": res.get("total_cost_usd"), "outputTokens": u.get("output_tokens"),
       "toolCalls": tools}
json.dump(rec, open(f"artifacts/{name}.usage.json", "w"), indent=2)
print(f"    turns: {rec['turns']}, tool calls: {tools}, cost: {rec['costUSD']} USD")
PY
