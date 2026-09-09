#!/usr/bin/env bash
# Uruchamia prompt z prompts/ przez claude -p i zapisuje transkrypt.
set -euo pipefail
PROMPT="${1:?podaj plik promptu}"
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
# Model bierzemy z frontmattera promptu, a nie z modelUsage - tam moga byc
# takze modele pomocnicze, co przy raportowaniu wprowadza w blad.
rec = {"model": model, "effort": effort, "turns": res.get("num_turns"),
       "costUSD": res.get("total_cost_usd"), "outputTokens": u.get("output_tokens"),
       "toolCalls": tools}
json.dump(rec, open(f"artifacts/{name}.usage.json", "w"), indent=2)
print(f"    tur: {rec['turns']}, wywolan narzedzi: {tools}, koszt: {rec['costUSD']} USD")
PY
