#!/usr/bin/env python3
"""
Zero-Scan MCP Server (core/mcp_server.py)
Model Context Protocol (MCP) Server for Zero-Scan Context Engine (.agent/ Project Memory).
Pure Python 3.11+ standard library implementation (zero external dependencies).
Enables instant integration with Cursor, Claude Desktop, Windsurf, Trae, and Claude Code.

Copyright (c) 2026 Chau Vu / CPF-FAMILY. Licensed under MIT.
"""

import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import core memory utilities
try:
    from core.memory import (
        MAX_BOOTSTRAP_CONTEXT_BYTES,
        add_decision_record,
        calculate_metrics,
        find_agent_dir,
        get_git_commit,
        get_git_status_summary,
        validate_agent_memory,
    )
except ImportError:
    from memory import (  # type: ignore
        MAX_BOOTSTRAP_CONTEXT_BYTES,
        add_decision_record,
        calculate_metrics,
        find_agent_dir,
        get_git_commit,
        get_git_status_summary,
        validate_agent_memory,
    )

SERVER_NAME = "zeroscan-mcp"
SERVER_VERSION = "2.2.1"
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "zeroscan_boot",
        "description": "Read the Level 0 Boot Anchor (.agent/BOOT.md) instantly (< 1 KB / ~500 tokens). Eliminates directory scanning overhead and provides immediate architectural orientation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository. Defaults to current working directory.",
                }
            },
        },
    },
    {
        "name": "zeroscan_get_map",
        "description": "Retrieve the structured GPS domain map (.agent/PROJECT_MAP.json). Shows domain modules, critical files, entry points, and test suites without directory crawling.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository.",
                }
            },
        },
    },
    {
        "name": "zeroscan_get_state",
        "description": "Retrieve project progress, completed milestones, git hash, and active branch state (.agent/PROJECT_STATE.json).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository.",
                }
            },
        },
    },
    {
        "name": "zeroscan_get_next_task",
        "description": "Read the immediate next task and atomic execution steps from .agent/NEXT_TASK.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository.",
                }
            },
        },
    },
    {
        "name": "zeroscan_record_decision",
        "description": "Append an Architectural Decision Record (ADR) into .agent/DECISIONS.md to preserve architectural consensus across AI agent sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Brief title of the architectural decision.",
                },
                "decision": {
                    "type": "string",
                    "description": "Details of the decision, rationale, and consequences.",
                },
                "author": {
                    "type": "string",
                    "description": "Author or Agent identifier (defaults to 'AI Agent').",
                },
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository.",
                },
            },
            "required": ["title", "decision"],
        },
    },
    {
        "name": "zeroscan_validate",
        "description": "Validate that the repository .agent/ directory conforms to the Zero-Scan specification and stays strictly within the <= 10 KB context budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Optional root directory path of the repository.",
                }
            },
        },
    },
]

PROMPTS = [
    {
        "name": "zeroscan_context_bootstrap",
        "description": "Bootstrap AI Coding Agent context using Zero-Scan Level 0 Boot Anchor and Next Task without reading the entire repository.",
        "arguments": [
            {
                "name": "task_description",
                "description": "Brief description of the task to be performed.",
                "required": False,
            }
        ],
    }
]


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {"listChanged": False},
            "prompts": {"listChanged": False},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


def get_default_workspace_root() -> Path:
    """Get default workspace root with fallback to environment variables (ZEROSCAN_PROJECT_ROOT, WORKSPACE_FOLDER)."""
    env_root = os.environ.get("ZEROSCAN_PROJECT_ROOT") or os.environ.get("WORKSPACE_FOLDER")
    if env_root and Path(env_root).is_dir():
        return Path(env_root).resolve()
    return Path.cwd().resolve()

def handle_tools_list() -> Dict[str, Any]:
    return {"tools": TOOLS}


def handle_prompts_list() -> Dict[str, Any]:
    return {"prompts": PROMPTS}


def handle_prompts_get(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if name == "zeroscan_context_bootstrap":
        agent_dir = find_agent_dir(get_default_workspace_root())
        boot_path = agent_dir / "BOOT.md"
        task_path = agent_dir / "NEXT_TASK.md"

        boot_content = boot_path.read_text(encoding="utf-8") if boot_path.is_file() else "No BOOT.md found."
        task_content = task_path.read_text(encoding="utf-8") if task_path.is_file() else "No NEXT_TASK.md found."

        return {
            "description": "Zero-Scan Zero-Token Context Bootstrap",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"You are an AI Coding Agent operating under Zero-Scan Project Memory V2.1.\n\n=== LEVEL 0 BOOT ANCHOR ===\n{boot_content}\n\n=== CURRENT NEXT TASK ===\n{task_content}\n\nDo NOT scan the full repository. Proceed with your task directly using this grounded context.",
                    },
                }
            ],
        }
    raise ValueError(f"Unknown prompt: {name}")


def resolve_safe_project_path(raw_path: Optional[str], root_boundary: Optional[Path] = None) -> Path:
    """Resolve and sandbox project path, preventing path traversal outside the project root."""
    default_root = get_default_workspace_root()
    boundary = (root_boundary or default_root).resolve()
    if not raw_path:
        return boundary
    try:
        candidate = Path(raw_path).resolve()
        # If explicit root boundary is enforced
        if root_boundary is not None:
            if candidate == boundary or boundary in candidate.parents:
                if candidate.is_dir():
                    return candidate
            return boundary
        # If no explicit root_boundary, allow valid existing project directories
        if candidate.is_dir():
            return candidate
        if candidate == boundary or boundary in candidate.parents:
            return candidate
    except Exception:
        pass
    return boundary


def handle_tools_call(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    args = arguments or {}
    project_path = resolve_safe_project_path(args.get("project_path"))
    agent_dir = find_agent_dir(project_path)

    if name == "zeroscan_boot":
        boot_file = agent_dir / "BOOT.md"
        if not boot_file.is_file():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: No .agent/BOOT.md found at {agent_dir}. Initialize with zeroscan bootstrap first.",
                    }
                ],
                "isError": True,
            }
        content = boot_file.read_text(encoding="utf-8")
        size_bytes = len(content.encode("utf-8"))
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Zero-Scan Boot Anchor ({size_bytes} bytes)\n\n{content}",
                }
            ]
        }

    elif name == "zeroscan_get_map":
        map_file = agent_dir / "PROJECT_MAP.json"
        if not map_file.is_file():
            return {
                "content": [{"type": "text", "text": f"Error: No .agent/PROJECT_MAP.json found at {agent_dir}."}],
                "isError": True,
            }
        content = map_file.read_text(encoding="utf-8")
        return {"content": [{"type": "text", "text": content}]}

    elif name == "zeroscan_get_state":
        state_file = agent_dir / "PROJECT_STATE.json"
        if not state_file.is_file():
            return {
                "content": [{"type": "text", "text": f"Error: No .agent/PROJECT_STATE.json found at {agent_dir}."}],
                "isError": True,
            }
        content = state_file.read_text(encoding="utf-8")
        return {"content": [{"type": "text", "text": content}]}

    elif name == "zeroscan_get_next_task":
        task_file = agent_dir / "NEXT_TASK.md"
        if not task_file.is_file():
            return {
                "content": [{"type": "text", "text": f"Error: No .agent/NEXT_TASK.md found at {agent_dir}."}],
                "isError": True,
            }
        content = task_file.read_text(encoding="utf-8")
        return {"content": [{"type": "text", "text": content}]}

    elif name == "zeroscan_record_decision":
        title = args["title"]
        decision = args["decision"]
        adr_id = args.get("id", f"ADR-{int(time.time())}")
        context = args.get("context", "")
        status = args.get("status", "LOCKED")
        add_decision_record(agent_dir, adr_id, title, decision, context=context, status=status)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully recorded ADR [{adr_id}: {title}] in {agent_dir / 'DECISIONS.md'}.",
                }
            ]
        }

    elif name == "zeroscan_validate":
        is_valid, errors, warnings = validate_agent_memory(agent_dir)
        metrics = calculate_metrics(agent_dir)
        size_bytes = metrics.get("bootstrap_context_bytes", 0)
        total_sys_bytes = metrics.get("total_agent_system_bytes", 0)
        pct = metrics.get("budget_used_percent", 0.0)

        status_text = (
            f"Zero-Scan Specification Validation:\n"
            f"- Status: {'PASS ✅' if is_valid else 'FAIL ❌'}\n"
            f"- Bootstrap Context Size: {size_bytes} / {MAX_BOOTSTRAP_CONTEXT_BYTES} bytes ({pct}% used, Budget <= 10 KB)\n"
            f"- Total Agent Memory Size: {total_sys_bytes} bytes\n"
            f"- Errors: {errors if errors else 'None'}\n"
            f"- Warnings: {warnings if warnings else 'None'}\n"
            f"- Location: {agent_dir}"
        )
        return {"content": [{"type": "text", "text": status_text}], "isError": not is_valid}

    raise ValueError(f"Unknown tool: {name}")


def run_stdio_server():
    """Main JSON-RPC stdio loop for MCP protocol."""
    while True:
        req_id = None
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                result = handle_initialize(params)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "notifications/initialized":
                continue  # No response required for notifications
            elif method == "tools/list":
                result = handle_tools_list()
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = handle_tools_call(tool_name, tool_args)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "prompts/list":
                result = handle_prompts_list()
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "prompts/get":
                prompt_name = params.get("name")
                prompt_args = params.get("arguments", {})
                result = handle_prompts_get(prompt_name, prompt_args)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            err_response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }
            sys.stdout.write(json.dumps(err_response) + "\n")
            sys.stdout.flush()


def main() -> int:
    """CLI entrypoint for zeroscan-mcp."""
    run_stdio_server()
    return 0


if __name__ == "__main__":
    sys.exit(main())
