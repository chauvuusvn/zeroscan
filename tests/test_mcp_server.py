#!/usr/bin/env python3
"""
Unit tests for Zero-Scan MCP Server (core/mcp_server.py).
Tests JSON-RPC protocol compliance and MCP tools.
"""

import json
import unittest
from pathlib import Path
from core.mcp_server import (
    handle_initialize,
    handle_prompts_get,
    handle_prompts_list,
    handle_tools_call,
    handle_tools_list,
)


ZEROSCAN_ROOT = str(Path(__file__).resolve().parent.parent)

class TestMCPServer(unittest.TestCase):
    def setUp(self):
        import os
        os.environ["ZEROSCAN_PROJECT_ROOT"] = ZEROSCAN_ROOT

    def test_initialize(self):
        resp = handle_initialize({})
        self.assertEqual(resp["protocolVersion"], "2024-11-05")
        self.assertEqual(resp["serverInfo"]["name"], "zeroscan-mcp")
        self.assertIn("tools", resp["capabilities"])

    def test_tools_list(self):
        resp = handle_tools_list()
        tools = resp.get("tools", [])
        tool_names = [t["name"] for t in tools]
        self.assertIn("zeroscan_boot", tool_names)
        self.assertIn("zeroscan_get_map", tool_names)
        self.assertIn("zeroscan_get_state", tool_names)
        self.assertIn("zeroscan_get_next_task", tool_names)
        self.assertIn("zeroscan_record_decision", tool_names)
        self.assertIn("zeroscan_validate", tool_names)
        self.assertEqual(len(tools), 6)

    def test_prompts_list_and_get(self):
        resp = handle_prompts_list()
        prompts = resp.get("prompts", [])
        self.assertTrue(any(p["name"] == "zeroscan_context_bootstrap" for p in prompts))

        prompt_data = handle_prompts_get("zeroscan_context_bootstrap")
        self.assertIn("messages", prompt_data)
        self.assertIn("LEVEL 0 BOOT ANCHOR", prompt_data["messages"][0]["content"]["text"])

    def test_tool_call_boot(self):
        resp = handle_tools_call("zeroscan_boot", {"project_path": ZEROSCAN_ROOT})
        self.assertIn("content", resp)
        self.assertTrue(len(resp["content"]) > 0)
        self.assertIn("Zero-Scan", resp["content"][0]["text"])

    def test_tool_call_validate(self):
        resp = handle_tools_call("zeroscan_validate", {"project_path": ZEROSCAN_ROOT})
        self.assertIn("content", resp)
        self.assertIn("Zero-Scan Specification Validation", resp["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
