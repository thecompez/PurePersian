"""Regression and protocol tests for PurePersian."""
from __future__ import annotations

import unittest

from purepersian_mcp import lexicon


class LexiconTests(unittest.TestCase):
    def test_entries_and_categories(self):
        metadata = lexicon.stats()
        self.assertEqual(metadata["entry_count"], 255)
        self.assertEqual(len(metadata["categories"]), 23)
        self.assertGreater(metadata["unique_term_count"], 200)

    def test_normalization_and_exact_lookup(self):
        self.assertEqual(lexicon.normalize("كلمه‌اي"), "کلمه ای")
        matches = lexicon.lookup("احتمالا")["matches"]
        self.assertTrue(any(m["term"] == "احتمالاً" and "شاید" in m["equivalents"] for m in matches))

    def test_disambiguation_and_reverse_lookup(self):
        result = lexicon.lookup("داده")
        self.assertGreaterEqual(len(result["matches"]), 2)
        self.assertTrue(all(m["matched_on"] in ("term", "equivalent_reverse") for m in result["matches"]))

    def test_search_ranking_and_empty(self):
        found = lexicon.search("دقیقاً")
        self.assertEqual(found["results"][0]["term"], "دقیقاً")
        self.assertEqual(lexicon.search("a-weird-word-not-in-dictionary")["total"], 0)

    def test_inspect_keeps_input(self):
        original = "احتمالا این مشکل مجدداً تکرار می‌شود."
        found = lexicon.inspect(original)
        self.assertFalse(found["auto_rewritten"])
        self.assertTrue(any(x["term"] == "احتمالاً" for x in found["matches"]))
        self.assertTrue(any(x["term"] == "مجدداً" for x in found["matches"]))
        self.assertTrue(all(x["requires_context_review"] for x in found["matches"]))

    def test_inspect_does_not_match_word_inside_word(self):
        self.assertFalse(any(x["term"] == "ابر" for x in lexicon.inspect("ابرها")["matches"]))

    def test_text_length_limit(self):
        with self.assertRaises(ValueError):
            lexicon.inspect("x" * 8001)


class MCPProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_in_memory_mcp_protocol(self):
        from mcp import Client
        from purepersian_mcp.server import mcp

        async with Client(mcp, raise_exceptions=True) as client:
            listing = await client.list_tools()
            tool_names = {tool.name for tool in listing.tools}
            self.assertEqual(
                tool_names,
                {"lookup_term", "search_terms", "list_categories", "glossary_stats", "inspect_text"},
            )
            resp = await client.call_tool("lookup_term", {"term": "دقیقاً"})
            self.assertFalse(resp.is_error)
            self.assertEqual(resp.structured_content["query"], "دقیقاً")
            scanned = await client.call_tool("inspect_text", {"text": "قطعاً، برای نمونه."})
            self.assertFalse(scanned.is_error)
            self.assertFalse(scanned.structured_content["auto_rewritten"])
            resources = await client.list_resources()
            resource_uris = {str(resource.uri) for resource in resources.resources}
            self.assertIn("purepersian://guide", resource_uris)
            self.assertIn("purepersian://stats", resource_uris)
            prompts = await client.list_prompts()
            self.assertIn("context_aware_rewrite", {prompt.name for prompt in prompts.prompts})


if __name__ == "__main__":
    unittest.main()
