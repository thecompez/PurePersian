---
name: purepersian
description: Improve or review Persian wording with context-sensitive PurePersian lexical suggestions; avoid automatic synonym substitution.
---

# PurePersian language skill

Use when a user explicitly wants Persian prose polished, Persian equivalents for loanwords,
a glossary entry explained, or terms checked against the PurePersian corpus.

## Steps
1. Consult `AGENTS.md`, `llms.txt` and, if connected, `purepersian://guide`.
2. Query `search_terms` or `lookup_term` for the exact word and inspect `usage` and `review_status`.
3. For passages, call `inspect_text`, then evaluate candidate meanings in context.
4. Rewrite naturally **only if the user requested a rewrite**. Preserve nuance, proper names and terms of art.
5. For disputed candidates show both options and a short explanation.
6. If the corpus has no entry, state that explicitly rather than inventing an attributed PurePersian replacement.

Never treat the MCP server as a text-generation model. It exposes read-only structured data.
