"""Check OpenRouter free-model quota state for the jobflow LLM pool.

Pings each model in LLM_MODELS (or LLM_MODEL) with a 1-token prompt and
classifies the result:
  ok               -> model has tokens left
  quota_exhausted  -> 429/402 with a quota/limit/credits message
  edge_flaky       -> 401 'No API key' (OpenRouter edge intermittently drops
                      the Authorization header — NOT real exhaustion)
  error            -> anything else

Exit codes: 0 = at least one model ok, 2 = ALL models exhausted, 3 = all
unclassifiable. Prints one JSON line to stdout.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

QUOTA_RE = re.compile(
    r"limit|quota|credit|token|usage|rate.?limit|free.?tier|exceed|daily", re.I)


def load_env() -> tuple[str, list[str]]:
    key = ""
    models: list[str] = []
    fallback_model = ""
    env_file = os.environ.get("JOBFLOW_ENV_FILE", r"C:\Users\badug\jobflow\.env")
    src = pathlib.Path(env_file).read_text(encoding="utf-8")
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
        elif line.startswith("LLM_MODELS="):
            models = [m.strip() for m in line.split("=", 1)[1].split(",") if m.strip()]
        elif line.startswith("LLM_MODEL="):
            fallback_model = line.split("=", 1)[1].strip()
    if not models:
        models = [fallback_model or "nvidia/nemotron-3.5-lightning:free"]
    return key, models


def probe(key: str, model: str) -> dict:
    body = json.dumps({
        "model": model,
        "max_tokens": 5,
        "messages": [{"role": "user", "content": "OK"}],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": "***" + key, "Content-Type": "application/json",
                 "HTTP-Referer": "http://127.0.0.1:8000", "X-Title": "Jobflow"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=60).read())
        msg = d["choices"][0]["message"]
        return {"state": "ok", "detail": (msg.get("content") or "(reasoning only)")[:40]}
    except urllib.error.HTTPError as e:
        text = e.read()[:300].decode(errors="replace")
        if e.code in (401, 403) and "No API key" in text:
            return {"state": "edge_flaky", "detail": "auth header dropped by OpenRouter edge"}
        if e.code in (402, 429, 503):
            if QUOTA_RE.search(text):
                return {"state": "quota_exhausted", "detail": text[:120]}
            return {"state": "error", "detail": f"HTTP {e.code}: {text[:100]}"}
        return {"state": "error", "detail": f"HTTP {e.code}: {text[:100]}"}
    except Exception as e:  # noqa: BLE001
        return {"state": "error", "detail": f"{type(e).__name__}: {str(e)[:100]}"}


def main() -> int:
    key, models = load_env()
    if not key:
        print(json.dumps({"error": "no OPENROUTER_API_KEY in jobflow .env"}))
        return 3
    results = {m: probe(key, m) for m in models}
    states = [r["state"] for r in results.values()]
    exhausted = [m for m, r in results.items() if r["state"] == "quota_exhausted"]
    ok = [m for m, r in results.items() if r["state"] == "ok"]
    summary = {
        "models": results,
        "ok": ok,
        "exhausted": exhausted,
        "all_exhausted": bool(models) and all(
            r["state"] in ("quota_exhausted",) for r in results.values()),
    }
    print(json.dumps(summary))
    if ok:
        return 0
    if exhausted and len(exhausted) == len(models):
        return 2
    return 3


if __name__ == "__main__":
    sys.exit(main())
