"""Small Streamable HTTP client for Epic's official local Unreal MCP server."""
from __future__ import annotations
import contextlib
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.parse
import urllib.request

class MCPError(RuntimeError):
    pass

def validate_url(url):
    p = urllib.parse.urlsplit(url)
    try:
        local = p.hostname == "localhost" or ipaddress.ip_address(p.hostname or "").is_loopback
    except ValueError:
        local = False
    if p.scheme != "http" or not local or p.username or p.password or p.query or p.fragment or p.path != "/mcp":
        raise MCPError("Use a loopback HTTP endpoint ending in /mcp, without credentials/query.")
    if not p.port:
        raise MCPError("Specify the local server port explicitly.")
    return url

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MCPError("MCP redirects are not allowed.")

def decode_response(raw, content_type):
    if not raw.strip():
        return None
    if "text/event-stream" not in content_type:
        return json.loads(raw)
    for event in raw.replace("\r\n", "\n").split("\n\n"):
        data = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
        if data:
            value = json.loads(data)
            if "result" in value or "error" in value:
                return value
    raise MCPError("SSE response contains no JSON-RPC result.")

@contextlib.contextmanager
def endpoint_lock(url, timeout=30):
    # Normalize loopback aliases so localhost and 127.0.0.1 share a lock.
    key = str(urllib.parse.urlsplit(url).port)
    path = Path(tempfile.gettempdir()) / ("unreal-codex-" + hashlib.sha256(key.encode()).hexdigest()[:16] + ".lock")
    with path.open("a+b") as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b"0"); f.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                f.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise MCPError("Another studio client owns the editor endpoint.")
                time.sleep(0.1)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)

def unpack(result):
    if result.get("isError"):
        raise MCPError(json.dumps(result, ensure_ascii=False))
    if "structuredContent" in result:
        return result["structuredContent"]
    texts = [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except ValueError:
            return texts[0]
    return result

class Client:
    def __init__(self, url, timeout=90):
        self.url = validate_url(url)
        self.timeout = timeout
        self.session = None
        self.protocol = "2025-03-26"
        self.counter = 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method, params=None, notification=False):
        self.counter += 1
        data = {"jsonrpc": "2.0", "method": method}
        if not notification:
            data["id"] = self.counter
        if params is not None:
            data["params"] = params
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        if method != "initialize":
            headers["MCP-Protocol-Version"] = self.protocol
        req = urllib.request.Request(self.url, json.dumps(data).encode(), headers)
        with self.opener.open(req, timeout=self.timeout) as response:
            self.session = response.headers.get("Mcp-Session-Id", self.session)
            value = decode_response(response.read().decode(), response.headers.get("Content-Type", ""))
        if notification:
            return None
        if not isinstance(value, dict) or value.get("id") != self.counter:
            raise MCPError("Unexpected JSON-RPC response ID.")
        if "error" in value:
            raise MCPError(json.dumps(value["error"], ensure_ascii=False))
        return value["result"]

    def initialize(self):
        info = self.request("initialize", {"protocolVersion": self.protocol, "capabilities": {},
            "clientInfo": {"name": "unreal-codex-studio", "version": "0.1.0"}})
        # Epic's installed 5.8.4 build returns empty serverInfo fields.
        # This is an identity hint, not authentication; bind the project separately.
        if info.get("serverInfo", {}).get("name") not in ("unreal-mcp", ""):
            raise MCPError("Endpoint is not the expected official unreal-mcp server.")
        self.protocol = info["protocolVersion"]
        self.request("notifications/initialized", notification=True)
        return info

    def tools(self):
        found, cursor = [], None
        while True:
            result = self.request("tools/list", {"cursor": cursor} if cursor else {})
            found.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return found

    def call(self, name, arguments=None):
        return unpack(self.request("tools/call", {"name": name, "arguments": arguments or {}}))
