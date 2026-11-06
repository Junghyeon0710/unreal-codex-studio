import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mcp_client import Client, MCPError, decode_response, endpoint_lock, validate_url, unpack
from studio import Unreal, ASSET, command_plan, connect, make_example, scan

spec = importlib.util.spec_from_file_location("guard", ROOT / ".codex/hooks/guard.py")
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.project = Path(make_example(self.folder / "Game")["project"])
    def tearDown(self):
        self.temp.cleanup()

class StudioTests(Fixture):
    def test_example_preserves_existing_destination(self):
        content = self.project.read_bytes()
        with self.assertRaises(ValueError):
            make_example(self.project.parent)
        self.assertEqual(content, self.project.read_bytes())

    def test_project_scan(self):
        source = self.project.parent / "Source"
        source.mkdir(); (source / "GameEditor.Target.cs").write_text("// fixture")
        result = scan(self.project)
        self.assertEqual(result["engine_association"], "5.8")
        self.assertEqual(len(result["targets"]), 1)
        self.assertEqual(result["source_files"], 1)

    def test_build_uses_explicit_target_and_preserves_path_argument(self):
        command = command_plan("build", self.folder / "Engine With Spaces", self.project, "GameEditor")
        self.assertEqual(command[1:4], ["GameEditor", "Win64", "Development"])
        self.assertEqual(command[4], str(self.project))
        with self.assertRaises(ValueError):
            command_plan("build", self.folder, self.project)

    def test_automation_filter_rejects_console_injection(self):
        with self.assertRaises(ValueError):
            command_plan("test", self.folder, self.project, test_filter="Tests; quit")
        good = command_plan("test", self.folder, self.project, test_filter="Game.Inventory")
        self.assertIn("-ExecCmds=Automation RunTests Game.Inventory", good)

    def test_package_requires_explicit_archive(self):
        with self.assertRaises(ValueError):
            command_plan("package", self.folder, self.project)

    def test_connect_preserves_unrelated_config(self):
        root = self.folder / "studio"; (root / ".codex").mkdir(parents=True)
        cfg = root / ".codex/config.toml"
        cfg.write_text('[agents]\nenabled = true\n[mcp_servers.unreal]\nurl = "old"\nenabled = false\ntool_timeout_sec = 75\ndefault_tools_approval_mode = "prompt"\n[mcp_servers.other]\nurl = "http://localhost:9000/mcp"\n')
        with patch("studio.ROOT", root):
            connect("http://127.0.0.1:8017/mcp")
        import tomllib
        result = tomllib.loads(cfg.read_text())
        self.assertEqual(result["mcp_servers"]["other"]["url"], "http://localhost:9000/mcp")
        self.assertTrue(result["mcp_servers"]["unreal"]["enabled"])
        self.assertEqual(result["mcp_servers"]["unreal"]["tool_timeout_sec"], 75)
        self.assertEqual(result["mcp_servers"]["unreal"]["default_tools_approval_mode"], "prompt")

    def test_binding_wrong_project_fails_and_cleans_challenge(self):
        ue = Unreal(None)
        with patch.object(ue, "call", return_value="different-project"):
            with self.assertRaises(MCPError):
                ue.bind(self.project)
        self.assertEqual(list((self.project.parent / "Saved/UnrealCodexStudio").glob("*")), [])

    def test_binding_reads_exact_challenge_and_cleans_it(self):
        ue = Unreal(None)
        def read_challenge(toolset, name, args):
            self.assertEqual((toolset, name), (ASSET, "read_file"))
            ue.events.append({"result": "temporary"})
            return Path(args["file_path"]).read_text()
        with patch.object(ue, "call", side_effect=read_challenge):
            self.assertEqual(ue.bind(self.project)["binding"], "verified")
        self.assertEqual(list((self.project.parent / "Saved/UnrealCodexStudio").glob("*")), [])
        self.assertEqual(ue.events[-1]["result"], "project challenge matched")

class TransportTests(unittest.TestCase):
    def test_loopback_only(self):
        for url in ["https://localhost:8000/mcp", "http://example.com:8000/mcp",
                    "http://127.0.0.1:8000/mcp?x=1", "http://user@localhost:8000/mcp",
                    "http://127.0.0.1/mcp", "http://localhost:8000/other"]:
            with self.subTest(url=url), self.assertRaises((MCPError, ValueError)):
                validate_url(url)
        self.assertEqual(validate_url("http://[::1]:8000/mcp"), "http://[::1]:8000/mcp")

    def test_sse_response_and_errors(self):
        result = decode_response('event: message\r\ndata: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\r\n\r\n', "text/event-stream")
        self.assertTrue(result["result"]["ok"])
        with self.assertRaises(MCPError):
            unpack({"isError": True, "content": [{"type": "text", "text": "failed"}]})

    def test_lock_rejects_overlapping_localhost_alias(self):
        with endpoint_lock("http://127.0.0.1:48991/mcp"):
            with self.assertRaises(MCPError):
                with endpoint_lock("http://localhost:48991/mcp", timeout=0):
                    pass

    def test_http_negotiation_session_and_tools(self):
        captured = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                captured.append((data, dict(self.headers)))
                if data["method"] == "initialize":
                    result = {"serverInfo": {"name": ""}, "protocolVersion": "2025-11-25", "capabilities": {}}
                elif data["method"] == "notifications/initialized":
                    self.send_response(202); self.end_headers(); return
                else:
                    result = {"tools": [{"name": "list_toolsets"}]}
                raw = json.dumps({"jsonrpc": "2.0", "id": data["id"], "result": result}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Mcp-Session-Id", "test-session"); self.send_header("Content-Length", str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            client = Client(f"http://127.0.0.1:{server.server_port}/mcp")
            client.initialize()
            self.assertEqual(client.tools()[0]["name"], "list_toolsets")
            headers = {k.lower(): v for k, v in captured[-1][1].items()}
            self.assertEqual(headers["mcp-session-id"], "test-session")
            self.assertEqual(headers["mcp-protocol-version"], "2025-11-25")
        finally:
            server.shutdown(); server.server_close(); worker.join()

    def test_unexpected_server_rejected(self):
        client = Client("http://localhost:8000/mcp")
        with patch.object(client, "request", return_value={"serverInfo": {"name": "other"}}):
            with self.assertRaises(MCPError):
                client.initialize()

class GuardTests(unittest.TestCase):
    def test_native_codex_command_payload(self):
        result = guard.evaluate({"hook_event_name": "PreToolUse", "tool_name": "apply_patch",
            "tool_input": {"command": "*** Begin Patch\n*** Add File: Content/Probe.uasset\n+text\n*** End Patch"}})
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_binary_patch_and_move_blocked(self):
        for line in ["*** Add File: Content/Test.uasset", "*** Update File: Map.UMAP",
                     "*** Move to: Moved.uasset", "*** Delete File: Level.umap"]:
            result = guard.evaluate({"hook_event_name": "PreToolUse", "tool_name": "apply_patch",
                "tool_input": "*** Begin Patch\n" + line + "\n*** End Patch"})
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_source_patch_not_blocked_and_no_permission_grant(self):
        self.assertEqual(guard.evaluate({"hook_event_name": "PreToolUse", "tool_name": "apply_patch",
            "tool_input": "*** Begin Patch\n*** Add File: Actor.cpp\n+// test\n*** End Patch"}), {})

if __name__ == "__main__":
    unittest.main()
