# Epic official Unreal MCP

This project connects to the MCP server installed with Unreal Engine. It does not
ship, reimplement or redistribute Epic's plugin.

## Enable and discover

Enable ModelContextProtocol (friendly name Unreal MCP) and AllToolsets in the
target .uproject using the editor plugin manager. Restart the editor. Run
`ModelContextProtocol.StartServer 8000` in the editor console, or launch with
`-ModelContextProtocolStartServer -ModelContextProtocolPort=8000`.
Default endpoint: `http://127.0.0.1:8000/mcp`.

Only connect locally. Epic's endpoint has no authentication. The fixture explicitly
sets HTTPServer.Listeners DefaultBindAddress=127.0.0.1; check your own listener
configuration before using a nonfixture project. Do not expose the server publicly.

Use list_toolsets, describe_toolset, then call_tool. Match exact discovered names,
required fields, enum values and returned refPath references. Tool descriptions may
be localized. APIs are Experimental and change between engine versions.

Official 5.8.4 observed here returns an empty serverInfo name/title/version and
negotiates protocol 2025-11-25. The client accepts an empty name or unreal-mcp, rejects
other names, and independently validates the selected project. Server metadata is
not authentication or proof of binary provenance.

## Project binding

`doctor --url ...` creates a random short-lived text challenge in the specified
project's Saved/UnrealCodexStudio directory, then reads it through the official
AssetTools.read_file tool. That tool restricts paths to the connected project's
allowed directories. The client requires an exact match and deletes its challenge.
A different project's endpoint fails before editor changes.

Generic CLI tool calls repeat binding immediately before execution. Native Codex
MCP calls bypass this Python wrapper, so the editor owner must run doctor first and
recheck if the server/editor restarts or its endpoint changes. This is an operational
guard, not a security boundary against a malicious local server.

## Concurrency

One editor owner handles MCP operations, including reads, sequentially.
The Python client uses a process lock per local port. This does not lock native
Codex calls or external clients; the coordinator must serialize those. Never let
two agents edit the same Blueprint, map or global PIE session concurrently.

## Codex configuration

tools/studio.py connect updates only the managed mcp_servers.unreal table in this
workspace's .codex/config.toml. It never writes global Codex settings. Native HTTP
MCP tools are available after trusting/reloading the project in a compatible host.
Model, sandbox and approval policy remain inherited.

The optional patch hook requires both hook support and explicit hook trust.
Review its implementation before trusting. It blocks apply_patch text operations
on .uasset/.umap; it cannot intercept every shell, MCP or filesystem operation and
must not be advertised as comprehensive protection.

## Sources

- [Epic: Unreal MCP in Unreal Editor](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
