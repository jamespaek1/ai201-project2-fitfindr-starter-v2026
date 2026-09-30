# FitFindr

James Paek · AI201 · Units 3–4

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

- **Transport in Unit 4:** `agent.py::search_listings` calls `mcp_client.call_tool`; `mcp_server.py::search_listings` exposes this one tool over stdio. The other two tools remain direct calls.
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

These are historical Unit 3 development observations. The Unit 4 evaluation, MCP migration and measured improvement are documented below.

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

**Unit 3 scope:** The preceding sample runs are the original Unit 3 evidence. No optional stretch feature is claimed. Unit 4 extends this same repository below.


**Unit 4 AI assistance:** At the user's request, Codex implemented the MCP wrapper
and trace instrumentation, ran the actual Gemini calls, reviewed the captions,
scored the saved evidence, and drafted this report. It did not change the original
criteria or claim the user performed these steps independently. The substantive
agent improvement is one rewritten `create_fit_card` system prompt. The model,
temperature, data, search logic, outfit prompt and targets stayed the same.

Two concrete decisions in this assisted workflow were to preserve and diagnose
the failed evidence-collector runs instead of presenting them as valid tests,
and to reject fluent captions that were too short or invented a seller. The
full outputs and per-caption reasoning remain available for independent review.

---

## Run Log — Before

The original criteria remain byte-for-byte unchanged from Unit 3 commit
`b113716`; no targets were revised. All five valid tries/cases were run again
after the improvement. Criteria 1 and 3 use separate sets of five complete
agent runs. Criterion 4 calls `tools.py::create_fit_card` directly with the
exact fixed listing and outfit in `criteria.md`. Criterion 5 uses the five
different searches specified there, once each, in the original table order;
it is not five repetitions of the first search.

Reproduce with `python run_eval.py --label before` and, after the prompt change,
`python run_eval.py --label after`. Labels refuse to overwrite existing evidence;
use a new label for a later independent run. The runner disables caching, keeps
temperature 0.9 and `gemini-3.5-flash-lite`, captures full inputs/returns, and
records actual model-call deltas, UTC timestamps, source hashes and the Git
revision. No recorded agent failure was retried until it passed or removed.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item reaches both later tools unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card is concise and grounded | 4 of 5 | FAIL | FAIL | FAIL | PASS | FAIL | MISSED (1/5) |
| 5. Size and budget survive ranking | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The valid before run made **25 model calls**, with 25 model calls this session, 14415 prompt + 2678 output tokens. The complete raw records are in [unit4_before.json](results/unit4_before.json)
and [unit4_before.md](results/unit4_before.md); progress and pacing are in
[the console log](results/unit4_before_console.txt). The JSON saves every session
and input, not just the final answer. The scorer and explicit grounding reviews
are [notes/score_evidence.py](notes/score_evidence.py) and
[unit4_before_grounding.json](results/unit4_before_grounding.json).

**Evidence-collector failures, retained separately:** Two preliminary collections
failed because the added log capture interfered with MCP subprocess stderr.
A `StringIO` has no `fileno`; changing to a temporary stderr file then exposed
the SDK's captured default argument retaining the first, closed file. The final
collector leaves stderr alone and captures stdout only. The agent's normal CLI
and MCP round-trip tests worked throughout. Both failed collections are retained
as [first attempt](results/unit4_harness_failure.json) and
[second attempt](results/unit4_harness_failure_2.json), with companion Markdown
and console logs. They made 5 and 7 real model calls, respectively; they are not
hidden, relabeled as successful agent tests, or included in the valid comparison.
The same corrected collector was used without changes for both valid runs.
Two integration tests now exercise repeated MCP calls through that collector.

### Actual output for each criterion

These are excerpts copied from the saved before-run values, without rewriting
the model's text. `run_eval.py::run_once` collected them. All omitted fields
are retained in the raw JSON.

**Criterion 1, try 1**

Produced by `agent.py::run_agent` → `tools.py::create_fit_card`:

```text
Channeling that ultimate effortless everyday streetwear vibe with a cropped Y2K Baby Tee — Butterfly Print paired with baggy dark-wash jeans. It is listed on depop for $18.00 and brings all the nostalgic early 2000s energy to your wardrobe rotation.
```

**Criterion 2, try 1**

Produced by `agent.py::run_agent`, empty-search branch after MCP:

```text
No listings matched 'designer ballgown' (size: XXS, max price: 5.0). Try broader keywords, another size, or a higher budget.
```
```json
{
  "search_results": [],
  "selected_item": null,
  "outfit_suggestion": null,
  "fit_card": null,
  "tool_calls": [
    {
      "tool": "search_listings",
      "inputs": {
        "description": "designer ballgown",
        "size": "XXS",
        "max_price": 5.0
      },
      "transport": "MCP/stdio",
      "returned": []
    }
  ]
}
```

**Criterion 3, try 1**

Produced by `agent.py::run_agent` and `_call`; full recorded item inputs (wardrobe fields omitted here):

```json
{
  "selected_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "search_results[0]": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "suggest_outfit.new_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "create_fit_card.inputs": {
    "outfit": "**Outfit 1: Y2K Streetwear**\nPair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash, and Chunky white sneakers. Complete the look with the Black crossbody bag and Vintage black denim jacket. \n*Style Pairing:* The fitted crop length of the butterfly tee balances the voluminous silhouette of the high-waisted baggy jeans for an authentic Y2K streetwear proportion, while the chunky sneakers and black denim jacket lean into the retro casual aesthetic.\n\n**Outfit 2: Casual Contrast**\nPair the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers and Black combat boots. Accessorize with the Brown leather belt.\n*Style Pairing:* The pink and purple butterfly graphic pops against the earthy tan trousers, while the lace-up combat boots add a tough, contrasting edge to the sweet cottagecore and vintage vibes of the baby tee.",
    "new_item": {
      "id": "lst_002",
      "title": "Y2K Baby Tee — Butterfly Print",
      "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
      "category": "tops",
      "style_tags": [
        "y2k",
        "vintage",
        "graphic tee",
        "cottagecore"
      ],
      "size": "S/M",
      "condition": "excellent",
      "price": 18.0,
      "colors": [
        "white",
        "pink",
        "purple"
      ],
      "brand": null,
      "platform": "depop"
    }
  },
  "outfit_suggestion": "**Outfit 1: Y2K Streetwear**\nPair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash, and Chunky white sneakers. Complete the look with the Black crossbody bag and Vintage black denim jacket. \n*Style Pairing:* The fitted crop length of the butterfly tee balances the voluminous silhouette of the high-waisted baggy jeans for an authentic Y2K streetwear proportion, while the chunky sneakers and black denim jacket lean into the retro casual aesthetic.\n\n**Outfit 2: Casual Contrast**\nPair the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers and Black combat boots. Accessorize with the Brown leather belt.\n*Style Pairing:* The pink and purple butterfly graphic pops against the earthy tan trousers, while the lace-up combat boots add a tough, contrasting edge to the sweet cottagecore and vintage vibes of the baby tee."
}
```

**Criterion 4, try 1**

Produced by `tools.py::create_fit_card`, with the original fixed outfit and `lst_002`:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It's priced at $18.00 and ready to list on depop.
```

**Criterion 5, try 1**

Produced by `mcp_server.py::search_listings` → `tools.py::search_listings`, decoded by `mcp_client.call_tool`:

```json
{
  "inputs": {
    "description": "graphic tee",
    "size": "M",
    "max_price": 18.0
  },
  "returned": [
    {
      "id": "lst_002",
      "title": "Y2K Baby Tee — Butterfly Print",
      "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
      "category": "tops",
      "style_tags": [
        "y2k",
        "vintage",
        "graphic tee",
        "cottagecore"
      ],
      "size": "S/M",
      "condition": "excellent",
      "price": 18.0,
      "colors": [
        "white",
        "pink",
        "purple"
      ],
      "brand": null,
      "platform": "depop"
    },
    {
      "id": "lst_017",
      "title": "Mesh Long-Sleeve Top — Black",
      "description": "Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.",
      "category": "tops",
      "style_tags": [
        "y2k",
        "grunge",
        "goth",
        "layering"
      ],
      "size": "S/M",
      "condition": "excellent",
      "price": 15.0,
      "colors": [
        "black"
      ],
      "brand": null,
      "platform": "depop"
    }
  ]
}
```

## Verdicts and Diagnoses

| Criterion | Before verdict | Reason |
|---|---|---|
| 1 | MET (5/5; target 4/5) | All five sessions have no error, nonempty fit cards and exactly the three required calls in order. A caption's factual quality is not silently added to this completion criterion. |
| 2 | MET (5/5; target 5/5) | All five sessions stop after search, keep later fields null, name changes the user can try, and make zero model calls. |
| 3 | MET (5/5; target 5/5) | In five separate complete runs, the full selected listing equals the first result and both recorded downstream item inputs; the saved outfit equals the caption input. |
| 4 | MISSED (1/5; target 4/5) | Only try 4 meets both the format bounds and the factual-grounding rule. Two tries have 28 words and two invent seller/availability claims. |
| 5 | MET (5/5; target 5/5) | Each original search returns its required listing, every returned source record fits the complete size label and inclusive price ceiling, and no model is called. |

**The missed criterion fails in model output from `tools.py::create_fit_card`,
not in search, the empty branch or session handoff.** The prompt's social-caption
framing allowed sales language even though a later negative instruction forbade
it; this is the likely prompt mechanism behind the observed seller claims.
The 30-word minimum also had no validation or repair, so a terse two-sentence
caption passed straight through at 28 words. These are two symptoms in one tool.

| Try | Words | Sentences | Decision and specific cause |
|---|---:|---:|---|
| 1 | 31 | 2 | FAIL — 'ready to list on depop' invents a seller/listing-readiness claim; the source is an existing mock listing, not an item the user is preparing to sell. |
| 2 | 28 | 2 | FAIL — Only the supplied outfit, exact title, price and platform are asserted. Fails separately because it has 28 words. |
| 3 | 47 | 3 | FAIL — 'Snag this piece' implies availability; 'my Depop shop' and 'more nostalgic finds' invent a seller identity and inventory. |
| 4 | 39 | 2 | PASS — The named pieces and listing facts are supplied. 'brings ... energy to your wardrobe' describes a styling benefit, without saying the user already bought or owns the listing. No invented brand, seller or availability claim. |
| 5 | 28 | 2 | FAIL — Only the supplied outfit, exact title, price and platform are asserted. Fails separately because it has 28 words. |

All five original captions, including the repeated output on tries 2 and 5:

Try 1:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It's priced at $18.00 and ready to list on depop.
```

Try 2:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It is listed on depop for $18.00.
```

Try 3:

```text
Channeling total early 2000s energy by styling the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers. It creates such a fun, playful look for everyday wear. Snag this piece for $18.00 and check out my Depop shop for more nostalgic finds!
```

Try 4:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It is listed on depop for $18.00 and brings all the best early-2000s nostalgic energy to your wardrobe.
```

Try 5:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. It is listed on depop for $18.00.
```

Each of those calls is separately recorded with one provider request and cache
disabled. Duplicate wording does not establish a cache hit. The punctuation
count ignores decimal-price periods, and a sentence-final period after `$18.00`
does not create an extra sentence or invalidate the price. Factual decisions
were made from complete captions, not inferred from the mechanical checks.

Criteria 1–3 and 5 had no misses; that does not prove general reliability.
A future criterion 4 target of **5/5** would be more suitable for a published
caption, and a broader follow-up test should cover other listings and adversarial
inputs. Neither proposal changes this unit's original 4/5 target.

## Loop Trace

This is the full diagnostic CLI run recorded **before the prompt improvement**.
It contains all three calls in order, exact inputs and outputs, the selected-item
step, and a finish step. The underlying data is supplied mock inventory.
Produced by `app.py::_ask_one` → `agent.py::run_agent` / `_call` → `trace.py::step`.

<details>
<summary>Full happy-path trace (actual terminal text)</summary>

```text
[1] parse_query
      in:  "vintage graphic tee under $30, size M"
      out: {
  "description": "vintage graphic tee",
  "size": "M",
  "max_price": 30.0
}
[2] search_listings (via MCP)
      in:  {
  "description": "vintage graphic tee",
  "size": "M",
  "max_price": 30.0
}
      out: [
  {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_017",
    "title": "Mesh Long-Sleeve Top — Black",
    "description": "Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "grunge",
      "goth",
      "layering"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 15.0,
    "colors": [
      "black"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_013",
    "title": "90s Silk Slip Dress — Floral, Midi Length",
    "description": "Delicate 90s slip dress in a muted floral print. Midi length, adjustable straps. Light snag on the side seam — not visible when worn.",
    "category": "bottoms",
    "style_tags": [
      "90s",
      "vintage",
      "feminine",
      "floral",
      "cottagecore"
    ],
    "size": "M",
    "condition": "good",
    "price": 30.0,
    "colors": [
      "ivory",
      "dusty pink",
      "green"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_020",
    "title": "Henley Long Sleeve — Washed Burgundy",
    "description": "Soft washed henley in a rich burgundy. Three-button placket. Slightly shrunken/cropped fit. 100% cotton.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "basics",
      "earth tones",
      "classic"
    ],
    "size": "M",
    "condition": "excellent",
    "price": 16.0,
    "colors": [
      "burgundy",
      "wine"
    ],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_024",
    "title": "Vintage Polo Shirt — Forest Green",
    "description": "Classic polo in forest green. Short sleeve, ribbed collar. Slightly boxy. The kind of piece that goes with everything.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "preppy",
      "classic",
      "earth tones"
    ],
    "size": "M",
    "condition": "good",
    "price": 18.0,
    "colors": [
      "green",
      "forest green"
    ],
    "brand": "Ralph Lauren",
    "platform": "thredUp"
  },
  {
    "id": "lst_029",
    "title": "Silk Button-Down — Sage Green",
    "description": "Loose silk (feel) button-down in sage green. Long sleeve, can be worn open as a layer or fully buttoned. Very flowy.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "minimal",
      "earth tones",
      "cottagecore"
    ],
    "size": "M",
    "condition": "excellent",
    "price": 28.0,
    "colors": [
      "sage",
      "green"
    ],
    "brand": null,
    "platform": "depop"
  },
  {
    "id": "lst_030",
    "title": "Vintage Knit Vest — Argyle Brown/Cream",
    "description": "Classic argyle knit vest in brown and cream. Fits medium. V-neck. Ideal for the dark academia or preppy vintage aesthetic.",
    "category": "tops",
    "style_tags": [
      "vintage",
      "preppy",
      "knitwear",
      "dark academia",
      "earth tones"
    ],
    "size": "M",
    "condition": "good",
    "price": 25.0,
    "colors": [
      "brown",
      "cream",
      "tan"
    ],
    "brand": null,
    "platform": "thredUp"
  },
  {
    "id": "lst_038",
    "title": "Denim Vest — Medium Wash, Studded",
    "description": "Denim vest with silver stud detailing along the collar and pockets. Classic rock-inspired customization. Fits like a medium.",
    "category": "outerwear",
    "style_tags": [
      "grunge",
      "vintage",
      "denim",
      "customized",
      "rock"
    ],
    "size": "M",
    "condition": "good",
    "price": 27.0,
    "colors": [
      "medium blue"
    ],
    "brand": null,
    "platform": "depop"
  }
]
[3] select first ranked result
      out: {
  "id": "lst_002",
  "title": "Y2K Baby Tee — Butterfly Print",
  "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
  "category": "tops",
  "style_tags": [
    "y2k",
    "vintage",
    "graphic tee",
    "cottagecore"
  ],
  "size": "S/M",
  "condition": "excellent",
  "price": 18.0,
  "colors": [
    "white",
    "pink",
    "purple"
  ],
  "brand": null,
  "platform": "depop"
}
[4] suggest_outfit
      in:  {
  "new_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  },
  "wardrobe": {
    "items": [
      {
        "id": "w_001",
        "name": "Baggy straight-leg jeans, dark wash",
        "category": "bottoms",
        "colors": [
          "dark blue",
          "indigo"
        ],
        "style_tags": [
          "denim",
          "streetwear",
          "baggy"
        ],
        "notes": "High-waisted, sits above the hip"
      },
      {
        "id": "w_002",
        "name": "Wide-leg khaki trousers",
        "category": "bottoms",
        "colors": [
          "khaki",
          "tan"
        ],
        "style_tags": [
          "earth tones",
          "minimal",
          "wide-leg"
        ],
        "notes": null
      },
      {
        "id": "w_003",
        "name": "White ribbed tank top",
        "category": "tops",
        "colors": [
          "white"
        ],
        "style_tags": [
          "basics",
          "minimal",
          "fitted"
        ],
        "notes": "Goes with everything"
      },
      {
        "id": "w_004",
        "name": "Oversized grey crewneck sweatshirt",
        "category": "tops",
        "colors": [
          "grey",
          "charcoal"
        ],
        "style_tags": [
          "oversized",
          "basics",
          "cozy"
        ],
        "notes": "Really oversized — drops below the hip"
      },
      {
        "id": "w_005",
        "name": "Black cropped zip hoodie",
        "category": "tops",
        "colors": [
          "black"
        ],
        "style_tags": [
          "athletic",
          "streetwear",
          "cropped"
        ],
        "notes": null
      },
      {
        "id": "w_006",
        "name": "Vintage black denim jacket",
        "category": "outerwear",
        "colors": [
          "black"
        ],
        "style_tags": [
          "denim",
          "vintage",
          "classic"
        ],
        "notes": "Slightly cropped"
      },
      {
        "id": "w_007",
        "name": "Chunky white sneakers",
        "category": "shoes",
        "colors": [
          "white"
        ],
        "style_tags": [
          "sneakers",
          "chunky",
          "streetwear"
        ],
        "notes": null
      },
      {
        "id": "w_008",
        "name": "Black combat boots",
        "category": "shoes",
        "colors": [
          "black"
        ],
        "style_tags": [
          "boots",
          "grunge",
          "classic"
        ],
        "notes": "Lace-up, mid-ankle height"
      },
      {
        "id": "w_009",
        "name": "Brown leather belt",
        "category": "accessories",
        "colors": [
          "brown"
        ],
        "style_tags": [
          "classic",
          "earth tones",
          "accessories"
        ],
        "notes": null
      },
      {
        "id": "w_010",
        "name": "Black crossbody bag",
        "category": "accessories",
        "colors": [
          "black"
        ],
        "style_tags": [
          "minimal",
          "accessories",
          "everyday"
        ],
        "notes": null
      }
    ]
  }
}
      out: "Outfit 1:\nPair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash and Chunky white sneakers. \nStyle pairing: The fitted crop length of the baby tee balances the volume of the high-waisted baggy jeans for a classic Y2K streetwear silhouette.\n\nOutfit 2:\nPair the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots.\nStyle pairing: The butterfly graphic tee brings a playful touch to earth-toned wide-leg trousers, while the cropped black denim jacket and lace-up boots add an edgy contrast."
[5] create_fit_card
      in:  {
  "outfit": "Outfit 1:\nPair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash and Chunky white sneakers. \nStyle pairing: The fitted crop length of the baby tee balances the volume of the high-waisted baggy jeans for a classic Y2K streetwear silhouette.\n\nOutfit 2:\nPair the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots.\nStyle pairing: The butterfly graphic tee brings a playful touch to earth-toned wide-leg trousers, while the cropped black denim jacket and lace-up boots add an edgy contrast.",
  "new_item": {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": [
      "y2k",
      "vintage",
      "graphic tee",
      "cottagecore"
    ],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.0,
    "colors": [
      "white",
      "pink",
      "purple"
    ],
    "brand": null,
    "platform": "depop"
  }
}
      out: "Channeling serious nostalgic energy with this Y2K Baby Tee — Butterfly Print listed on depop for $18.00. I love styling it with baggy straight-leg jeans and chunky white sneakers for that ultimate effortless streetwear vibe. It brings such a fun, playful pop of early 2000s color to your everyday rotation."
[6] finish
      →    All three tools completed; fit card saved in session.

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
Pair the Y2K Baby Tee — Butterfly Print with the Baggy straight-leg jeans, dark wash and Chunky white sneakers.
Style pairing: The fitted crop length of the baby tee balances the volume of the high-waisted baggy jeans for a classic Y2K streetwear silhouette.

Outfit 2:
Pair the Y2K Baby Tee — Butterfly Print with the Wide-leg khaki trousers, Vintage black denim jacket, and Black combat boots.
Style pairing: The butterfly graphic tee brings a playful touch to earth-toned wide-leg trousers, while the cropped black denim jacket and lace-up boots add an edgy contrast.

  Fit card: Channeling serious nostalgic energy with this Y2K Baby Tee — Butterfly Print listed on depop for $18.00. I love styling it with baggy straight-leg jeans and chunky white sneakers for that ultimate effortless streetwear vibe. It brings such a fun, playful pop of early 2000s color to your everyday rotation.

2 model calls this session, 1235 prompt + 206 output tokens

```

</details>

**Empty-search trace**

```text
[1] parse_query
      in:  "designer ballgown size XXS under $5"
      out: {
  "description": "designer ballgown",
  "size": "XXS",
  "max_price": 5.0
}
[2] search_listings (via MCP)
      in:  {
  "description": "designer ballgown",
  "size": "XXS",
  "max_price": 5.0
}
      out: []
[3] stop
      →    branch: empty search; No listings matched 'designer ballgown' (size: XXS, max price: 5.0). Try broader keywords, another size, or a higher budget.

  No listings matched 'designer ballgown' (size: XXS, max price: 5.0). Try broader keywords, another size, or a higher budget.

0 model calls this session

```

**On the MCP move:** `agent.py::search_listings` now calls
`mcp_client.call_tool("search_listings", arguments)`; the server delegates to the
original search implementation. Exactly one tool is registered. The SDK provides
typed input validation and the client unwraps the structured list result.
The full records, order, null brands and empty-list shape match direct search
in real subprocess integration checks. A subprocess is started per search, so
there is extra transport overhead. The two Gemini tools remain direct calls.
No search behavior was changed.

### Three deliberately triggered failure modes

- **Empty search:** the impossible query prints the message above and stops
  before either model tool (zero model calls).
- **Empty wardrobe:** the `--empty-wardrobe` run returned useful, explicitly
  hypothetical pairings. Actual `suggest_outfit` text follows.
- **Model unavailable:** `diagnostics.py` changes exactly one character of the
  key only in a child process environment. The saved `.env` is never edited or
  printed. The real provider rejects it, the agent catches `ModelUnavailable`,
  and the CLI returns actionable text without a raw stack trace. A subsequent
  happy-path call with the original key confirms normal operation.

```text
Because your wardrobe is currently empty, these are just suggestions and not items you currently own.

For the Y2K Baby Tee with a butterfly print, lean into its fitted, cropped silhouette with high-contrast proportions.

**Possible Pairings:**
1. **Low-Rise Baggy Jeans:** Pair the fitted white, pink, and purple tee with baggy low-rise denim to nail the Y2K aesthetic.
2. **A-Line Mini Skirt:** Style the graphic top with a simple denim or pleated mini skirt for a playful, vintage-inspired look.
```

```text
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

The user can broaden the search, try one of the suggested outfit pairings or
save wardrobe items, and check/create the API key, respectively. All three
messages name the condition and a next action. The existing Unit 3 handlers
already handled these cases, so they were retained rather than changed as a
second improvement. The old empty-wardrobe caption also says “You can grab,”
which reinforces the caption-grounding issue; it is preserved in the diagnostic
log, not presented as a factual success.

## The Improvement

**One behavior change:** rewrite the system prompt in
`tools.py::create_fit_card` (commit `80f6ca3`). It now asks for a hypothetical
outfit caption, aims for three sentences and 45–60 words within the unchanged
2–4 / 30–80 criterion, and attributes price/platform to the mock source record.
It explicitly contrasts neutral attribution with the seller phrases observed
in the before output. The actual input JSON and return handling are unchanged.
There is no added retry, postprocessor, fallback caption or additional branch.

The exact same five scenarios were collected after that change. The raw
[after JSON](results/unit4_after.json), [after Markdown](results/unit4_after.md),
[console output](results/unit4_after_console.txt), and
[grounding reviews](results/unit4_after_grounding.json) retain every attempt.
The before/after source hashes match for the evaluator, scenarios, criteria,
model configuration, adapter, agent and MCP code; only `tools.py` differs.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item reaches both later tools unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card is concise and grounded | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Size and budget survive ranking | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

| Criterion | Before passes | After passes | Target |
|---|---:|---:|---|
| 1. Matching query completes all three tools | 5/5 | 5/5 | 4/5 |
| 2. Impossible query stops before tool 2 | 5/5 | 5/5 | 5/5 |
| 3. Selected item reaches both later tools unchanged | 5/5 | 5/5 | 5/5 |
| 4. Fit card is concise and grounded | 1/5 | 5/5 | 4/5 |
| 5. Size and budget survive ranking | 5/5 | 5/5 | 5/5 |

**After-run caption checks:**

| Try | Words | Sentences | Grounding review | Result |
|---|---:|---:|---|---|
| 1 | 46 | 3 | Uses the supplied tee, jeans and sneakers; the fitted/Y2K styling follows the listing and outfit. Price and platform are attributed to the mock record, without seller, availability or ownership claims. | PASS |
| 2 | 47 | 3 | Fitted silhouette and relaxed denim are supported by the item and baggy-jeans outfit. All listing facts are exact and no shop, availability, brand or purchase is invented. | PASS |
| 3 | 46 | 3 | The fitted graphic top and relaxed denim contrast are grounded in the supplied description and outfit. Neutral source attribution makes no ownership, seller or availability claim. | PASS |
| 4 | 42 | 3 | Fitted crop length and the graphic print are supplied item details. The caption uses the specified outfit and attributes price/platform to the mock source without unsupported claims. | PASS |
| 5 | 44 | 3 | Retro styling and contrasting silhouettes are interpretations of the supplied Y2K tee and baggy-jeans outfit. The exact listing facts are attributed, with no invented brand, seller, availability or ownership. | PASS |

Actual after try 1, `tools.py::create_fit_card`:

```text
Pair the Y2K Baby Tee — Butterfly Print with dark-wash baggy jeans and chunky white sneakers for a playful Y2K look. This combination captures a nostalgic millennium aesthetic defined by fitted silhouettes and casual streetwear staples. The mock listing records a price of $18.00 on depop.
```

**Did it help?** In these runs, yes: the caption criterion rose from **1/5 to
5/5**, crossing its unchanged 4/5 target. The other four remained 5/5. The after
run made 25 model calls, the same as before, with no additional retry mechanism.
Five trials are a small sample; this observation does not establish a reliable
production failure rate or isolate the effect from all model randomness.

Provider-reported usage: before `25 model calls this session, 14415 prompt + 2678 output tokens`; after `25 model calls this session, 16295 prompt + 3083 output tokens`. The longer prompt increases input tokens, and the more explicit wording sounds less like a casual sales caption.

## What's Still Broken

No original criterion remains missed in the five after tries. The original
criteria and the full history remain intact. Passing this small test does not
mean the system is finished:

- Caption grounding still relies on a prompt. A separate deterministic format
  validator and a bounded repair could address length, while factual-review
  tests should include many listings. This unit stops after the one measured
  prompt change so its result remains interpretable.
- Search is lexical. A mesh top that mentions a graphic tee can appear as a
  secondary result. No semantic-search or ranking change was made this unit.
- The model adapter can still exhaust provider quota, and there is no new
  end-to-end timeout policy. Only the required invalid-key outage was exercised
  against the real provider; the test does not cover every outage type.
- Criterion 4 examines one listing and one outfit. A future stricter target
  would require 5/5 grounded captions across varied listings, including null
  brands and empty wardrobes. The original target is not rewritten retroactively.

The first follow-up would be broader caption-grounding tests before changing
more agent behavior, because fluent unsupported sales claims were the actual
observed failure. No optional stretch feature is claimed.

### Reproduction and evidence index

All 25 offline development/integration tests pass, including real MCP subprocess
round trips and repeated evidence collection. See [final test output](results/unit4_final_tests.txt).
README excerpts normalize trailing whitespace only; raw result files preserve the original text.

```sh
source .venv/bin/activate
python test.py
python mcp_client.py
python -m unittest discover -s tests -v
python diagnostics.py
python app.py ask 'vintage graphic tee under $30, size M' --trace
python run_eval.py --label independent_check
```

For the exact historical before behavior, checkout commit `c3a544e` in a separate
checkout and supply an ignored `.env`; the first valid before run itself records
`d77d1b2` and source hashes. The after code records `80f6ca3`. Do not overwrite
the existing evidence files. `notes/score_evidence.py` recomputes mechanical
checks from the saved data and incorporates the explicit per-caption grounding
notes; it does not create replacement results.

At least four new Unit 4 commits are present, with MCP, failure/trace work,
evidence collection, retained collector fixes, before results, the single prompt
change and the after report represented separately. All deliverables are text;
no screenshot or video is part of the assignment evidence. The same repository
URL is used for both Units 3 and 4.

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
