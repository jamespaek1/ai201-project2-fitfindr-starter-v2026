"""Integration checks use a real MCP subprocess; no Gemini requests."""

import unittest
from mcp_client import call_tool, MCPError
from tools import search_listings


class MCPIntegrationTests(unittest.TestCase):
    def test_round_trip_preserves_full_records_and_empty_list(self):
        for args in [
            {"description": "graphic tee", "size": "M", "max_price": 18.0},
            {"description": "designer ballgown", "size": "XXS", "max_price": 5.0},
        ]:
            with self.subTest(args=args):
                self.assertEqual(call_tool("search_listings", args), search_listings(**args))

    def test_invalid_budget_is_a_readable_protocol_error(self):
        with self.assertRaises(MCPError):
            call_tool("search_listings", {"description": "tee", "max_price": -1})
