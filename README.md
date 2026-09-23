# FitFindr

James Paek · AI201 · Unit 3

Built with Codex assistance. Implementation, specs, and the custom criteria
were drafted by Codex at the user's request; no independent student authorship
is claimed. The assignment asks students to author criteria themselves, so the
three custom criteria below are explicitly AI-assisted examples for review.
The specs and criteria are committed before implementation and model samples.

Setup and every starter command: [RUNNING.md](RUNNING.md), unchanged.
Use Python 3.11–3.13, install `requirements.txt` in `.venv`, and put your own
`GEMINI_API_KEY` in the ignored `.env`. Quote queries with single quotes:
`python app.py ask 'vintage graphic tee under $30, size M'`.

## What This Does

FitFindr accepts a thrift-shopping request with keywords and optional size and
budget, then searches 40 supplied mock listings. It selects the strongest
keyword match, asks Gemini how to combine it with the supplied wardrobe, and
asks Gemini for a short fit-card caption. Each result is saved in a session
before the next tool reads it; an empty search stops with suggestions for
changing the request. This is a local demonstration using fictional listings,
not a live marketplace search or a purchase service.

## Tool Inventory

### `search_listings`

- **What it does:** Load the supplied listings through `utils.data_loader.load_listings`, filter size and inclusive price ceiling, and rank by distinct keyword matches.
- **Inputs:** `description: str`, `size: str | None = None`, `max_price: float | None = None`.
- **Returns:** Up to `config.SEARCH_RESULT_LIMIT` original listing dicts, each containing `id`, `title`, `description`, `category`, `style_tags: list[str]`, `size`, `condition`, numeric `price`, `colors: list[str]`, nullable `brand`, and `platform`. Case-insensitive word tokens are matched against title, description, category, tags, colors, and non-null brand. Each distinct overlapping keyword counts once; zero-score records are dropped, descending score wins, and ID breaks ties. Common request filler is ignored; a small explicit plural map normalizes tees, jackets, shirts, shoes, sneakers, boots, dresses, and bags. This is lexical matching, not semantic search; partial keyword overlap can return a related item.
- **When it has nothing:** Return `[]`, including a blank/filler-only description. Invalid negative or non-finite prices raise `ValueError` rather than silently removing the budget.

Size matching is case-insensitive and compares complete labels: `M` matches
`S/M` and `M/L`, while `L` does not match `XL` and `S` does not match `US 9`.
Parenthetical fit notes are removed. A numeric shoe query such as `8.5` matches
`US 8.5`; no conversion between shoe sizing systems is attempted. `W30` matches
`W30 L30`; a query with both waist and length must match both. `One Size` matches
one-size labels only; it is not automatically substituted for requested sizes.

### `suggest_outfit`

- **What it does:** Call the starter's `generate.generate` adapter for one or two combinations using the new item and the supplied wardrobe.
- **Inputs:** `new_item: dict` (a listing in the shape above), `wardrobe: dict` with `items: list[dict]`. Each wardrobe item has `id`, `name`, `category`, `colors`, `style_tags`, and optional nullable `notes`.
- **Returns:** A stripped, non-empty `str` describing outfits; the prompt names actual wardrobe pieces and treats null brand as unknown. Listing and wardrobe text are data, not instructions.
- **When it has nothing:** For `{"items": []}`, still call the model for general styling suggestions, explicitly without claiming the user owns those pieces. A missing new item returns a descriptive message without a model call. Empty model text raises `ModelUnavailable`; provider failures propagate that same adapter exception.

### `create_fit_card`

- **What it does:** Call the same adapter to turn a supported outfit into a short social caption.
- **Inputs:** `outfit: str`, `new_item: dict` (the same selected listing).
- **Returns:** A stripped `str`, prompted to contain 2–4 sentences, 30–80 words, the exact listing title, dollar price, and platform once each, and a concrete outfit/vibe detail. It must not invent a brand, availability, ownership, or purchase. These are output-quality targets, not guaranteed postprocessing.
- **When it has nothing:** Empty or whitespace-only outfit returns `No fit card: add an outfit suggestion first.` without a model call. Missing item returns a descriptive message. Empty model text raises `ModelUnavailable`, as do provider failures.

## Planning Loop

**Branch rule:** If `search_listings` returns `[]`, set an error naming the
requested filters and suggest broader keywords, another size, or a higher
budget, then stop before `suggest_outfit`. Otherwise select the first result,
save it, obtain the outfit suggestion, then create the fit card.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** `agent.py::parse_query` uses regular expressions,
not a model call. Supported budget phrases include `under $30`, `below 30`,
`up to $30`, `at most $30`, and `max $30`; the ceiling is inclusive. Use an
explicit `size` phrase for a size, such as `size M`, `size US 8.5`, or
`size W30 L30`. Missing filters are `None`. Invalid stated budgets and an empty
description stop with guidance instead of a silently unbounded search.

**What moves through the session:** `query` and `wardrobe` → `parsed` →
`search_results` → `selected_item` → `outfit_suggestion` → `fit_card`.
The next action is chosen by a `while` loop after inspecting these fields;
results are never passed directly from one tool call into another. The session
also stores `tool_calls` with snapshots of actual inputs and returns so item
handoff can be checked independently of the final caption. Every iteration
calls `trace.check_iterations`; `config.MAX_ITERATIONS` bounds the loop.
Malformed queries and unavailable/empty model output produce an error in the
returned session, preserving completed stages. These are basic stopping
conditions; no stretch feature is claimed.

## Sample Run

Implementation and real tool samples are pending at this specification commit.
They will replace this paragraph after the tools and loop are run. See
[notes/unit3_build.md](notes/unit3_build.md) for the untouched starter output
and data inspection.

## How I Used AI

This section will record two concrete implementation decisions and actual
validation evidence as the work occurs. The request was “complete the
assignment on project unit 3.” Codex is performing the implementation and
writing; the eventual account will distinguish that from manual student work.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
