"""PurePersian MCP server (SDK v2; stdio transport, read-only)."""
from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.server import MCPServer
from pydantic import Field

from . import lexicon

mcp = MCPServer(
    "PurePersian",
    instructions=(
        "Read-only Persian glossary. All suggestions require contextual review. "
        "Never automatically replace technical terms, proper names, or words with "
        "different certainty/meaning. Use the purepersian://guide resource first."
    ),
)


@mcp.tool()
def lookup_term(term: Annotated[str, Field(min_length=1, max_length=120, description="Persian source term or equivalent to look up.")]) -> dict[str, Any]:
    """Find exact Persian terms and labelled reverse equivalence matches; return all senses."""
    return lexicon.lookup(term)


@mcp.tool()
def search_terms(
    query: Annotated[str, Field(min_length=1, max_length=120, description="Persian or English search string.")],
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
    category: str = "",
) -> dict[str, Any]:
    """Search term, proposed alternatives, English and usage notes; sorted by lexical relevance."""
    return lexicon.search(query, limit=limit, category=category)


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """List glossary topic sections and how many entries each includes."""
    return lexicon.categories()


@mcp.tool()
def glossary_stats() -> dict[str, Any]:
    """Return count, schema version, corpus sources, and agent safety guidance."""
    return lexicon.stats()


@mcp.tool()
def inspect_text(
    text: Annotated[str, Field(min_length=1, max_length=8000, description="Text to scan for possible glossary expressions; never rewritten.")],
    limit: Annotated[int, Field(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    """Identify candidate expressions and offsets WITHOUT modifying text or selecting a substitute."""
    return lexicon.inspect(text, limit=limit)


@mcp.resource("purepersian://guide")
def usage_guide() -> str:
    """Policy for careful, context-aware Persian rewriting by agents."""
    return lexicon.guide()


@mcp.resource("purepersian://stats")
def glossary_metadata() -> str:
    """Machine-readable catalogue summary."""
    return json.dumps(lexicon.stats(), ensure_ascii=False)


@mcp.prompt()
def context_aware_rewrite(text: str, register: str = "روان و طبیعی") -> str:
    """Provide a context-sensitive rewriting workflow for a Persian text."""
    return (
        "بازنویسی فارسی با حفظ معنا، لحن، زمان، درجهٔ قطعیت و اصطلاح‌های تخصصی.\n"
        "ابتدا با inspect_text نامزدها را شناسایی کن؛ برای هر واژهٔ مبهم lookup_term "
        "را بررسی کن. برابرهای پیشنهادی را جایگزین قطعی ندان؛ فقط گزینهٔ طبیعی و "
        "هم‌معنای مناسب با بافت را به‌کار ببر. نام‌های خاص و شناسه‌های کد را دست‌نزن.\n"
        f"شیوهٔ نگارش: {register}\n"
        f"متن:\n{text}\n"
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
