# PurePersian — AGENTS.md

## Purpose
PurePersian is a context-sensitive *proposal* glossary for Persian. It is not a language model,
a certified etymological lexicon, or a deterministic translation/replacement rule engine.

## Ground-truth order
1. Read usage guidance in this document and `purepersian://guide`.
2. Use MCP `lookup_term` for an exact word; it can return multiple meanings/categories.
3. Use `search_terms` to discover relevant terms, with an optional category filter.
4. Use `inspect_text` to identify possible word choices in text; its output is **never a rewrite**.
5. The authoritative editorial source is `persian.tex` plus `adverbs.tex`.
   The generated `purepersian_mcp/lexicon.json` is a machine-readable copy, not a separate source of truth.

## Semantic safeguards
- Never assume every suggested alternative is fully synonymous in all contexts.
- Preserve legal, scientific, financial, religious, and programming terminology, proper names,
  user quotations, identifiers and API names unless the user specifically asks to adapt them.
- Preserve certainty, negation, chronology, intent, voice, register and connotation.
- Example: «اصلاً» is not always «هرگز»; «احتمالاً» is not always «شاید»;
  «رمزنگاری» is different from «نهان‌نگاری».
- If a term has multiple editorial senses or conflicting options, explain the distinction.
- `review_status: legacy` means the historical suggestion has not been comprehensively verified.
  Treat all entries as editorial proposals, not established linguistic claims.
- If a requested phrase has no entry, **do not fabricate a PurePersian citation or claim it is in the corpus**.
- When explaining a suggestion, mention its `source` and `usage` when useful.

## Contributor workflow
- Update the *appropriate LaTeX table* first, maintaining four columns:
  `واژهٔ رایج & برابر فارسی & انگلیسی & توضیح کاربرد \\\\ `.
- Existing 18 sections: `persian.tex`; adverb sections: `adverbs.tex`.
- Run `python tools/export_lexicon.py` to regenerate the packaged JSON.
- Run `python tools/export_lexicon.py --check` and `python -m unittest discover -s tests -v`.
- Do not edit `purepersian_mcp/lexicon.json` by hand.
- Keep the MCP server read-only and free of unsolicited network calls and automatic text mutations.
- The PDF must be built with XeLaTeX and **Vazirmatn v33.003** installed;
  CI downloads the original font at build time (no font binaries are stored here).
