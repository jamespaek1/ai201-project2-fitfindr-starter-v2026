"""Expose the existing listing search through MCP over standard input/output."""

from mcp.server.fastmcp import FastMCP
from tools import search_listings as _search_listings_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(description: str, size: str | None = None,
                    max_price: float | None = None) -> list[dict]:
    """Search mock thrift listings by keywords, optional complete size label and
    inclusive maximum price in US dollars; return ranked listing objects, or []
    when no listing matches the requested keywords and filters. If the result
    is [], tell the user to try broader keywords in description, change or omit
    size, or increase max_price, then search again with their revised request.
    Decimal prices are allowed; negative or nonfinite budgets are rejected.
    This searches supplied data, not live inventory.
    """
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()
