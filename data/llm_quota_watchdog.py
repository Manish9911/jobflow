"""Cron watchdog: announce OpenRouter free-model token exhaustion.

Runs every tick; prints NOTHING while at least one free model has tokens
(silent = healthy). Prints a short alert only when one or both models report
quota_exhausted, so the user knows when to switch to the local
qwen-3.8-27b endpoint. OpenRouter's flaky edge (401 'No API key') is NOT
treated as exhaustion — at most one gentle note per state change, never
repeated while the state is unchanged.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import check_llm_quota as cq  # noqa: E402

STATE_FILE = HERE / "llm_quota_state.json"


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(d: dict) -> None:
    STATE_FILE.write_text(json.dumps(d, indent=1), encoding="utf-8")


def main() -> None:
    try:
        key, models = cq.load_env()
        results = {m: cq.probe(key, m) for m in models}
    except Exception:
        return  # can't even read the key — stay silent
    states = {m: r["state"] for m, r in results.items()}
    exhausted = [m for m, s in states.items() if s == "quota_exhausted"]
    prev = load_state().get("exhausted", [])

    if exhausted and len(exhausted) == len(models):
        sig = "ALL"
        if sig != prev:
            print(
                "Both OpenRouter free models are OUT of tokens: "
                + ", ".join(exhausted)
                + ". Free tier is exhausted for today — time to switch to the "
                  "local qwen-3.8-27b endpoint (alias: local-qwen). Say "
                  "'switch to qwen' and I'll flip the config."
            )
            save_state({"exhausted": "ALL"})
    elif exhausted:
        sig = ",".join(sorted(exhausted))
        if sig != prev:
            print(
                "Heads-up: " + ", ".join(exhausted)
                + " is out of free tokens; the other model is still covering "
                  "traffic. If both go quiet, I'll ping you to switch to "
                  "local qwen-3.8-27b."
            )
            save_state({"exhausted": sig})
    else:
        # recovered or healthy — clear state so the next exhaustion re-announces
        if prev:
            save_state({"exhausted": []})


if __name__ == "__main__":
    main()
