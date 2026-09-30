"""FitFindr's bounded planning loop and observable session handoff."""

from copy import deepcopy
import math
import re

import trace
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError
from tools import suggest_outfit, create_fit_card


def search_listings(description: str, size: str | None = None,
                    max_price: float | None = None) -> list[dict]:
    """Keep the existing loop contract, with search transported through MCP."""
    return call_tool("search_listings", {
        "description": description, "size": size, "max_price": max_price,
    })

_PRICE = re.compile(
    r"\b(?:under|below|up\s+to|at\s+most|max(?:imum)?(?:\s+price)?)"
    r"\s*\$?\s*(?P<price>[-+]?(?:\d+(?:\.\d+)?|\.\d+))(?![\w.])", re.I)
_SIZE = re.compile(
    r"\bsize\s+(?P<size>one\s+size|W\d+(?:\s+L\d+)?|"
    r"(?:US\s+)?\d+(?:\.\d+)?|[a-z]{1,5}(?:/[a-z]{1,5})?)(?![\w.])", re.I)


def parse_query(query: str) -> dict:
    """Parse the documented size/budget syntax without calling a model."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Describe an item, for example 'graphic tee under $30, size M'.")
    prices = list(_PRICE.finditer(query))
    sizes = list(_SIZE.finditer(query))
    if len(prices) > 1 or len(sizes) > 1:
        raise ValueError("Use one size and one price ceiling per query.")
    max_price = float(prices[0]['price']) if prices else None
    if max_price is not None and (not math.isfinite(max_price) or max_price < 0):
        raise ValueError("Use a finite non-negative budget, for example 'under $30'.")
    size = sizes[0]['size'].upper() if sizes else None
    remainder = _SIZE.sub(' ', _PRICE.sub(' ', query))
    if re.search(r"\b(?:under|below|up\s+to|at\s+most|max(?:imum)?|size)\b|\$", remainder, re.I):
        raise ValueError("Use filters like 'under $30' and 'size M' (one of each).")
    description = ' '.join(re.sub(r"[,;]", ' ', remainder).split()).strip()
    if not description:
        raise ValueError("Add item keywords, such as 'graphic tee', before the filters.")
    return {"description": description, "size": size, "max_price": max_price}


def new_session(query: str, wardrobe: dict) -> dict:
    """Create independent state; snapshots make downstream inputs inspectable."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": deepcopy(wardrobe),
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
        "tool_calls": [],
        "iterations": 0,
    }


def _call(session: dict, function, **inputs):
    entry = {"tool": function.__name__, "inputs": deepcopy(inputs)}
    entry["transport"] = "MCP/stdio" if function.__name__ == "search_listings" else "direct"
    session["tool_calls"].append(entry)
    step_name = function.__name__ + (" (via MCP)" if entry["transport"] == "MCP/stdio" else "")
    try:
        result = function(**inputs)
    except Exception as exc:
        entry["error"] = str(exc)
        trace.step(step_name, inputs=inputs, note=f"failed: {exc}", full=True)
        raise
    entry["returned"] = deepcopy(result)
    trace.step(step_name, inputs=inputs, returned=result, full=True)
    return result


def run_agent(query: str, wardrobe: dict) -> dict:
    """Choose the next tool from saved results; stop on empty search or error."""
    session = new_session(query, wardrobe)
    try:
        session["parsed"] = parse_query(session["query"])
        trace.step("parse_query", inputs=query, returned=session["parsed"], full=True)
    except ValueError as exc:
        session["error"] = str(exc)
        return session

    searched = False
    while session["fit_card"] is None and session["error"] is None:
        session["iterations"] += 1
        trace.check_iterations(session["iterations"])
        try:
            if not searched:
                session["search_results"] = _call(session, search_listings, **session["parsed"])
                searched = True
                if not session["search_results"]:
                    parsed = session["parsed"]
                    session["error"] = (
                        f"No listings matched {parsed['description']!r} "
                        f"(size: {parsed['size'] or 'any'}, "
                        f"max price: {parsed['max_price'] if parsed['max_price'] is not None else 'none'}). "
                        "Try broader keywords, another size, or a higher budget."
                    )
                    trace.step("stop", note="branch: empty search; " + session["error"])
                    break
                session["selected_item"] = session["search_results"][0]
                trace.step("select first ranked result", returned=session["selected_item"], full=True)
            elif session["outfit_suggestion"] is None:
                session["outfit_suggestion"] = _call(
                    session, suggest_outfit,
                    new_item=session["selected_item"], wardrobe=session["wardrobe"])
                if not session["outfit_suggestion"].strip():
                    session["error"] = "No outfit was returned. Try the request again."
            else:
                session["fit_card"] = _call(
                    session, create_fit_card,
                    outfit=session["outfit_suggestion"], new_item=session["selected_item"])
                if not session["fit_card"].strip():
                    session["fit_card"] = None
                    session["error"] = "No fit card was returned. Try the request again."
        except (ModelUnavailable, MCPError) as exc:
            session["error"] = str(exc)
            trace.step("stop", note="tool failure; " + session["error"])
    if session["fit_card"] is not None:
        trace.step("finish", note="All three tools completed; fit card saved in session.")
    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
