#!/usr/bin/env python3
"""Minimal cross-platform stdio client for the official RedFox MCP bridge."""

import argparse
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from redfox_runtime import has_api_key, load_env_file, write_or_print


PROTOCOL_VERSION = "2024-11-05"
DEFAULT_COMMAND = "uvx redfox-mcp"


def command_parts(command=None):
    command = command or os.getenv("REDFOX_MCP_COMMAND")
    if command:
        return shlex.split(command, posix=os.name != "nt")
    launcher = shutil.which("uvx")
    if not launcher:
        sibling = Path(sys.executable).parent / ("uvx.exe" if os.name == "nt" else "uvx")
        launcher = str(sibling) if sibling.is_file() else "uvx"
    return [launcher, "redfox-mcp"]


def annotate_tool(tool):
    result = dict(tool)
    description = str(tool.get("description", ""))
    if "优质库" in description or "premium" in description.lower():
        price_class = "quality"
    elif "实时" in description or "realtime" in description.lower():
        price_class = "realtime"
    else:
        price_class = "unknown"
    result["yuntu"] = {"transport": "mcp", "price_class": price_class}
    return result


def tool_search(tools, query, platform=None, limit=20):
    tokens = [token.lower() for token in query.split() if token.strip()]
    ranked = []
    for tool in tools:
        name = str(tool.get("name", ""))
        if platform and not name.startswith(f"{platform}_"):
            continue
        haystack = json.dumps(tool, ensure_ascii=False).lower()
        score = sum(1 for token in tokens if token in haystack) if tokens else 1
        if score:
            ranked.append((score, name, tool))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [tool for _, _, tool in ranked[:limit]]


class StdioMcpClient:
    def __init__(self, command=None, timeout=60):
        self.command = command_parts(command)
        self.timeout = timeout
        self.request_id = 0
        self.messages = queue.Queue()
        self.process = None

    def start(self):
        executable = shutil.which(self.command[0])
        if not executable:
            raise RuntimeError(f"MCP launcher not found: {self.command[0]}")
        env = os.environ.copy()
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        self.request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "yuntu-media-research", "version": "1.0.0"},
        })
        self.notify("notifications/initialized", {})
        return self

    def _read_stdout(self):
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    def _send(self, payload):
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP process is not running")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.request_id += 1
        request_id = self.request_id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(f"MCP request timed out: {method}")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise RuntimeError(f"MCP request timed out: {method}") from exc
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
            return message.get("result", {})

    def notify(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def list_tools(self):
        tools = []
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self.request("tools/list", params)
            tools.extend(annotate_tool(tool) for tool in result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, name, arguments):
        return self.request("tools/call", {"name": name, "arguments": arguments})

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", help="Optional env file override")
    parser.add_argument("--command", help="Override REDFOX_MCP_COMMAND, for example: uvx redfox-mcp")
    parser.add_argument("--timeout", type=int, default=60)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    list_parser = sub.add_parser("list-tools")
    list_parser.add_argument("--out")
    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("--query", default="")
    discover_parser.add_argument("--platform")
    discover_parser.add_argument("--limit", type=int, default=20)
    discover_parser.add_argument("--out")
    call_parser = sub.add_parser("call")
    call_parser.add_argument("--tool", required=True)
    call_parser.add_argument("--args", default="{}")
    call_parser.add_argument("--args-file")
    call_parser.add_argument("--out")
    call_parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    load_env_file(args.env_file)
    parts = command_parts(args.command)
    if args.action == "status":
        write_or_print({
            "has_api_key": has_api_key(),
            "command": parts,
            "launcher_available": bool(shutil.which(parts[0])),
        })
        return 0
    try:
        if args.action == "call" and not args.execute:
            raw_args = open(args.args_file, encoding="utf-8").read() if args.args_file else args.args
            write_or_print({"dry_run": True, "tool": args.tool, "arguments": json.loads(raw_args), "estimated_requests": 1})
            return 0
        with StdioMcpClient(args.command, args.timeout) as client:
            if args.action == "list-tools":
                write_or_print(client.list_tools(), args.out)
            elif args.action == "discover":
                write_or_print(tool_search(client.list_tools(), args.query, args.platform, args.limit), args.out)
            elif args.action == "call":
                raw_args = open(args.args_file, encoding="utf-8").read() if args.args_file else args.args
                arguments = json.loads(raw_args)
                if not isinstance(arguments, dict):
                    raise ValueError("args must be a JSON object")
                write_or_print(client.call_tool(args.tool, arguments), args.out)
        return 0
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
