"""Dismiss the blocking JS alert on the Garmin iCIMS tab via raw CDP websocket."""
import json
import urllib.request

tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9334/json", timeout=10))
target = next(t for t in tabs if "careers-garmin.icims.com" in t.get("url", ""))
ws_url = target["webSocketDebuggerUrl"]

import websocket  # noqa: E402

ws = websocket.create_connection(ws_url, timeout=15)


def cmd(mid, method, params=None):
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        d = json.loads(ws.recv())
        if d.get("id") == mid:
            return d


print("enable:", cmd(1, "Page.enable").get("result", {}))
print("handle:", cmd(2, "Page.handleDialog", {"accept": True}))
# verify
print("eval:", cmd(3, "Runtime.evaluate",
                     {"expression": "document.title + ' | bodylen=' + (document.body ? document.body.innerText.length : -1)",
                      "returnByValue": True}).get("result", {}).get("result", {}).get("value"))
ws.close()
