# FitFindr

James Paek · AI201 · Unit 3

Repository for Units 3 and 4: [jamespaek1/ai201-project2-fitfindr-starter-v2026](https://github.com/jamespaek1/ai201-project2-fitfindr-starter-v2026).

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

**Full agent query — actual CLI output**

Produced by `app.py::_ask_one` → `agent.py::run_agent` → the three functions in
`tools.py`, using `gemini-3.5-flash-lite`. Caching was off; this run made two
real model calls. The output below is copied without editing from
[`results/unit3_sample_run.txt`](results/unit3_sample_run.txt).

```text
$ AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear Contrast**
*   **Top:** Y2K Baby Tee — Butterfly Print (NEW_ITEM)
*   **Bottoms:** Baggy straight-leg jeans, dark wash (w_001)
*   **Shoes:** Chunky white sneakers (w_007)
*   **Accessories:** Black crossbody bag (w_010)
*   **Style Pairing:** Balance the fitted, cropped silhouette of the butterfly baby tee with high-waisted, baggy straight-leg jeans for an effortless Y2K streetwear look, finished with chunky white sneakers and a minimal black bag.

**Outfit 2: Casual Vintage Mix**
*   **Top:** Y2K Baby Tee — Butterfly Print (NEW_ITEM)
*   **Outerwear:** Vintage black denim jacket (w_006)
*   **Bottoms:** Wide-leg khaki trousers (w_002)
*   **Shoes:** Chunky white sneakers (w_007)
*   **Style Pairing:** Layer the cropped graphic baby tee under a slightly cropped vintage black denim jacket, pairing the pink and purple butterfly print with earthy wide-leg khaki trousers and white sneakers for a playful contrast of textures and styles.

  Fit card: Balancing a cropped silhouette with dark wash baggy straight-leg jeans gives off the ultimate effortless Y2K streetwear vibe. This Y2K Baby Tee — Butterfly Print is listed on depop for $18.00 and is such a fun piece to style.

2 model calls this session, 1367 prompt + 321 output tokens
```

**Session handoff and empty search**

Run `python app.py ask 'vintage graphic tee under $30, size M' --session`
to print the session after the answer. The recorded uncached run is in
[`results/unit3_agent_happy.txt`](results/unit3_agent_happy.txt), with its
extracted JSON in [`results/unit3_session_happy.json`](results/unit3_session_happy.json).
It selected `lst_002` in three loop iterations. The full listing dictionaries
in `search_results[0]`, `selected_item`, and both downstream `new_item` inputs
were compared and are equal, including null brand, size, and price. The fit
card tool also received exactly the saved `outfit_suggestion` string.

The impossible query `designer ballgown size XXS under $5` printed:

```text
No listings matched 'designer ballgown' (size: XXS, max price: 5.0). Try broader keywords, another size, or a higher budget.
```

Its [full printed session](results/unit3_agent_empty.txt) contains one tool call
(`search_listings`) and one loop iteration. `selected_item`,
`outfit_suggestion`, and `fit_card` remain `null`; model calls were zero.
The [empty-wardrobe run](results/unit3_agent_empty_wardrobe.txt) completed all
three tools and clearly labeled the pairings as suggestions.

These are development observations. Unit 4's five-try acceptance evaluation,
MCP migration, and before/after report have not been performed.

**Three tools tested separately, before wiring the loop**

These are actual terminal results, not illustrative outputs. Caching was
disabled. The two generation tools each made one real Gemini request.

```text
$ AI201_CACHE=0 python -c 'from tools import search_listings; print(search_listings('"'"'graphic tee'"'"', size='"'"'M'"'"', max_price=18)); import generate; print(generate.usage())'
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}]
0 model calls this session
```

```text
$ AI201_CACHE=0 python -c 'from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[1], get_example_wardrobe())); import generate; print(generate.usage())'
**Outfit 1: Y2K Streetwear Contrast**
Pair the Y2K Baby Tee with the Baggy straight-leg jeans, dark wash and Chunky white sneakers. Layer on the Black cropped zip hoodie and complete the look with the Black crossbody bag. 

**Style pairing:** The fitted, cropped silhouette of the butterfly baby tee balances the loose, high-waisted fit of the dark denim, capturing a classic Y2K streetwear vibe. Adding the cropped zip hoodie and chunky sneakers keeps the athletic, nostalgic aesthetic cohesive.

**Outfit 2: Casual Vintage Mix**
Style the Y2K Baby Tee with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots. 

**Style pairing:** The pink, purple, and white butterfly graphics pop against the neutral earth tones of the wide-leg khaki trousers. Layering the slightly cropped vintage black denim jacket and grounding the outfit with lace-up combat boots adds an edgy grunge contrast to the cute, fitted top.
1 model calls this session, 814 prompt + 205 output tokens
```

```text
$ AI201_CACHE=0 python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('"'"'Pair the butterfly tee with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look.'"'"', load_listings()[1])); import generate; print(generate.usage())'
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It is listed on depop for $18.00 and brings all the best early 2000s energy to your wardrobe.
1 model calls this session, 305 prompt + 58 output tokens
```

The same fit-card input produced three distinct captions at temperature 0.9.
All three raw outputs are saved in `results/unit3_tool_fit_card_*.txt`. The
third says "ready to shop", which implies availability the mock record does
not establish. That is an observed model-quality limitation, not a guarantee
that criterion 4 passes. No formal five-try evaluation was run.

The empty-wardrobe run returned general suggestions and explicitly said they
were not owned items; see `results/unit3_tool_empty_wardrobe.txt`. Search also
returned a mesh top whose description mentions layering under a graphic tee.
This shows the documented partial-keyword behavior; the actual graphic tee
ranked first.

The environment check passed all 10 checks, including a real model call.
Twelve offline development tests passed before wiring the loop; all 21
tool, parser, and loop tests passed after integration. Run them with
`python -m unittest discover -s tests -v`. Full raw
results are in `results/`; setup and source data are unchanged.

## How I Used AI

The user's request was “complete the assignment on project unit 3.” Codex read
the assignment, drafted the specs and criteria, implemented the code, ran the
commands, and prepared this account. The two moments below describe that actual
assisted workflow; they do not claim the user manually wrote or edited code.

**Moment 1 — translating the dataset into a search contract**

- **What was requested:** Complete the three specified tools over the supplied listings. Codex first inspected six whole listings, all size labels, and the wardrobe schema.
- **What came back:** The data showed `S/M`, `XL (oversized)`, `US 9`, `W30 L30`, and 32 null brands. A plain substring comparison would incorrectly make `L` match `XL` and `S` match `US 9`.
- **What changed:** Codex replaced the search stub with complete-label size matching, an inclusive price filter, and deterministic token-overlap ranking. The spec was committed first, and tests check the actual records at their price ceilings. No semantic matching or live shopping capability is claimed.

**Moment 2 — checking model variation and state rather than trusting fluent text**

- **What was requested:** The actual `create_fit_card` prompt asks for 2–4 sentences and 30–80 words, the exact title, price, and platform once each, with no invented facts. Codex also implemented the assignment's requirement to pass values through the session.
- **What came back:** Three real uncached model calls produced different captions for the same tee and outfit; one said “ready to shop,” an unsupported availability implication. The separate end-to-end run returned a caption and a session containing each actual tool input and return.
- **What changed:** Codex used `AI201_CACHE=0` for evidence runs, added `--session` and input snapshots to make the handoff visible, compared the saved item with both downstream inputs, and recorded the caption issue here. It did not replace the observed output with an idealized answer or claim that three varying captions prove the five-try criterion.

**Criteria assistance:** The course supplies criteria 1–2 and asks students to
write 3–5 themselves. Codex drafted 3–5 and all five explanations as explicit
teaching examples, committed before implementation and model samples. That
assistance is disclosed in `criteria.md`; independent student authorship is not
claimed. The original targets remain intact for Unit 4.

**Scope and status:** All Unit 3 implementation and README sections are filled,
with real terminal evidence and more than four milestone commits. No optional
stretch feature is claimed. The Unit 4 starter sections below are intentionally
left unchanged for the next assignment; their empty tables are not results.

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
