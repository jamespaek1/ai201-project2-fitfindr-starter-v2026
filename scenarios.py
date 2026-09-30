"""Exact scenarios from the unchanged Unit 3 criteria, not looser substitutes."""

MATCHING_QUERY = "vintage graphic tee under $30, size M"
FIXED_OUTFIT = (
    "Pair the butterfly tee with dark-wash baggy jeans and "
    "chunky white sneakers for a playful Y2K look."
)
SIZE_CASES = [
    {"description": "graphic tee", "size": "M", "max_price": 18.0, "expected": "lst_002"},
    {"description": "flannel", "size": "XL", "max_price": 22.0, "expected": "lst_003"},
    {"description": "jeans", "size": "W30", "max_price": 38.0, "expected": "lst_001"},
    {"description": "track jacket", "size": "M", "max_price": 45.0, "expected": "lst_004"},
    {"description": "graphic tee", "size": "L", "max_price": 24.0, "expected": "lst_006"},
]
SCENARIOS = [
    {"name": "Matching query completes all three tools", "criterion": 1, "target": 4,
     "kind": "agent", "query": MATCHING_QUERY},
    {"name": "Impossible query stops before tool 2", "criterion": 2, "target": 5,
     "kind": "agent", "query": "designer ballgown size XXS under $5"},
    {"name": "Selected item reaches both later tools unchanged", "criterion": 3, "target": 5,
     "kind": "agent", "query": MATCHING_QUERY},
    {"name": "Fit card is concise and grounded", "criterion": 4, "target": 4,
     "kind": "fit_card", "item_id": "lst_002", "outfit": FIXED_OUTFIT},
    {"name": "Size and budget survive ranking", "criterion": 5, "target": 5,
     "kind": "search_cases", "cases": SIZE_CASES},
]


def validate():
    problems = []
    if [s["criterion"] for s in SCENARIOS] != [1, 2, 3, 4, 5]:
        problems.append("Scenarios must cover original criteria 1–5, in order.")
    for scenario in SCENARIOS:
        if scenario["kind"] == "agent" and not scenario.get("query"):
            problems.append("An agent scenario needs a query.")
    return problems
