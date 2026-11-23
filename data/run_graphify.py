"""Run a graphify build for jobflow using the free OpenRouter backend.

Usage: python data/run_graphify.py [extra graphify args...]
Reads the OpenRouter key from jobflow/.env, maps it onto the openai backend
(OpenAI-compatible base URL + model), and runs graphify in the repo root.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = re.search(
    r"^OPENROUTER_API_KEY=(.+)$",
    (ROOT / ".env").read_text(encoding="utf-8"),
    re.M,
).group(1).strip()

env = dict(
    os.environ,
    OPENAI_BASE_URL="https://openrouter.ai/api/v1",
    OPENAI_API_KEY=KEY,
    OPENAI_MODEL="nvidia/nemotron-3.5-lightning:free",
)
cmd = ["graphify", ".", "--backend", "openai"] + sys.argv[1:]
r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1500, cwd=ROOT)
print(r.stdout[-2500:])
print("STDERR:", r.stderr[-1200:])
print("exit:", r.returncode)
sys.exit(r.returncode)
