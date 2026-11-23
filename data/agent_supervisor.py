"""Agent supervisor (2026-11-11): keeps the auto-apply agent running.

User instruction: "run the agent without failing anywhere in the run; if it
does [fall over], restart the agent again; don't re-apply already-applied
jobs (the agent's _HANDLED_STATUSES mechanism does that); complete as many
companies as possible."

What this does, every 30s:
- if the SERVER is down -> restart the detached uvicorn (max 5 times)
- if the AGENT thread died (running=false) -> restart it (max 10 times),
  logging last_error + last_activity for post-mortem
- stats snapshot every 10 min

Already-applied protection is the agent's own: every job with a handled
status (submitted / submit_uncertain / rejected_* / captcha_manual /
failed / ...) is never re-processed, so restarts can never double-apply.

Stop: kill this process (process_manage) and POST /api/agent/stop — the
supervisor only restarts things it believes should be running.
"""
import json
import subprocess
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
POLL_S = 30
SNAPSHOT_EVERY = 20          # 20 * 30s = 10 min
MAX_AGENT_RESTARTS = 10
MAX_SERVER_RESTARTS = 5

SERVER_CMD = [
    "powershell", "-NoProfile", "-Command",
    "Start-Process -FilePath 'C:\\Users\\badug\\jobflow\\.venv\\Scripts\\python.exe' "
    "-ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' "
    "-WorkingDirectory 'C:\\Users\\badug\\jobflow' -WindowStyle Hidden "
    "-RedirectStandardOutput 'C:\\Users\\badug\\jobflow\\data\\server_stdout.log' "
    "-RedirectStandardError 'C:\\Users\\badug\\jobflow\\data\\server_stderr.log'",
]


def log(msg: str) -> None:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def get(path: str, timeout: int = 10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def server_up() -> bool:
    try:
        get("/health", timeout=5)
        return True
    except Exception:
        return False


def start_server() -> None:
    log("restarting uvicorn (detached)")
    subprocess.Popen(SERVER_CMD, shell=False)
    for _ in range(24):
        time.sleep(5)
        if server_up():
            log("server back up")
            return
    log("WARNING: server did not come back within 120s")


def start_agent() -> dict:
    req = urllib.request.Request(
        BASE + "/api/agent/start?min_score=0", data=b"{}",
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def main() -> None:
    agent_restarts = 0
    server_restarts = 0
    tick = 0
    log("supervisor starting (agent restart cap "
        f"{MAX_AGENT_RESTARTS}, server restart cap {MAX_SERVER_RESTARTS})")

    if not server_up():
        server_restarts += 1
        start_server()

    try:
        r = start_agent()
        log(f"agent started: {r}")
    except Exception as e:
        log(f"initial agent start failed: {type(e).__name__}: {e}")

    while True:
        time.sleep(POLL_S)
        tick += 1

        if not server_up():
            server_restarts += 1
            log(f"server DOWN (restart {server_restarts}/{MAX_SERVER_RESTARTS})")
            if server_restarts > MAX_SERVER_RESTARTS:
                log("GIVING UP: too many server restarts")
                return
            start_server()
            continue

        try:
            st = get("/api/agent/status")
        except Exception as e:
            log(f"status fetch failed: {type(e).__name__}: {e}")
            continue

        if not st.get("running"):
            agent_restarts += 1
            log(f"AGENT NOT RUNNING (restart {agent_restarts}/{MAX_AGENT_RESTARTS}) "
                f"| last_error={st.get('last_error')!r} | "
                f"last_activity={st.get('last_activity')!r} | stats={st.get('stats')}")
            if agent_restarts > MAX_AGENT_RESTARTS:
                log("GIVING UP: agent restart cap reached")
                return
            time.sleep(5)
            try:
                r = start_agent()
                log(f"agent restarted: {r}")
            except Exception as e:
                log(f"agent restart failed: {type(e).__name__}: {e}")

        if tick % SNAPSHOT_EVERY == 0:
            log(f"stats: {st.get('stats')} | last: {st.get('last_activity')} | "
                f"error: {st.get('last_error')}")


if __name__ == "__main__":
    main()
