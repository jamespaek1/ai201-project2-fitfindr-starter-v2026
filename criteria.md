# Acceptance criteria — FitFindr, Unit 3

Written and committed before tool implementation, tool tests, and sample agent
runs. The starter was run only to confirm its unimplemented starting state.
Criteria 1–2 are supplied by the course. Criteria 3–5 and the explanations are
**Codex-drafted teaching examples**, not a claim that James authored them
independently. The assignment asks students to write their own criteria; this
assistance is disclosed for review. No Unit 4 acceptance verdicts are claimed.

For future evaluation, disable caching (`AI201_CACHE=0`) and keep
`TEMPERATURE=0.9`. A failed model request counts as a failed try, not an omitted
try. Keep all attempts and their sessions. The checks below define the intended
five-try evaluation; Unit 3 unit tests and sample runs are development checks.

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

Use `vintage graphic tee under $30, size M` and the example wardrobe for all five
tries. A pass has no session error, a nonempty string in `fit_card`, and exactly
`search_listings`, `suggest_outfit`, `create_fit_card` in `tool_calls`, in order.

**Why this target:** Search and selection should be deterministic, but this
path makes two network/model requests. Four of five tolerates one transient
provider or empty-output failure while still requiring a usable result most
of the time; stricter five of five would confound loop reliability with service
availability. A complete chain does not establish caption quality: criterion 4
checks that separately.

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

Use `designer ballgown size XXS under $5` five times. A pass contains only
`search_listings` in `tool_calls`, `search_results == []`, and `selected_item`,
`outfit_suggestion`, and `fit_card` all still `None`. The error must explicitly
suggest broader keywords, another size, or a higher budget. Check that the
adapter's model-call counter does not increase.

**Why this target:** No provider request is needed. The branch is a comparison
against a deterministic empty list, so tolerating a miss would allow needless
model calls and invented recommendations from nonexistent inventory. Five of
five is already the strictest success rate.

## 3. The selected item reaches both later tools unchanged

For five independent runs of the matching query from criterion 1, the full
listing dict in `session["selected_item"]` must equal
`session["search_results"][0]`, the actual `new_item` input recorded for
`suggest_outfit`, and the actual `new_item` input recorded for `create_fit_card`,
including `id`, `title`, `size`, `price`, and nullable `brand` — **5 of 5 tries**.
The recorded outfit input to `create_fit_card` must also exactly equal
`session["outfit_suggestion"]`. A missing downstream call fails that try.

**Why this target:** The handoff uses stored Python values, not a model's
recollection. A changed ID or price can produce a plausible caption for the
wrong purchase, so no mismatch is acceptable. Full input snapshots are needed:
checking only the final caption would miss errors hidden by fluent wording.

## 4. A fit card is concise and grounded despite varied wording

Call `create_fit_card` five times without caching for listing `lst_002` and this
same outfit string: `Pair the butterfly tee with dark-wash baggy jeans and
chunky white sneakers for a playful Y2K look.` At least **4 of 5 captions** must
meet **all** of these checks: 2–4 sentences, 30–80 whitespace-delimited words,
the exact listing title once, its price as `$18` or `$18.00` once, its platform
`depop` once (case-insensitive), and at least one named outfit piece (jeans or
sneakers). There must be no invented brand, seller claim, availability claim,
or claim that the user bought/owns the new listing.

Count sentences by terminal `.`, `!`, or `?`, treating decimal prices as part
of a number, and manually check ambiguous punctuation. Save the complete text
so another reader can review factual claims. Word-for-word variation is welcome
but is not itself a pass condition.

**Why this target:** The model can vary expression without varying facts. The
word and sentence bounds keep a caption readable, while required price,
platform, and item facts keep it useful. Four of five allows an occasional
formatting miss at nonzero temperature; a tighter guarantee would require
validation/retries beyond this initial build. Factual invention fails the whole
try rather than being averaged away.

## 5. Size and budget constraints survive ranking

Run each of these five searches once. **5 of 5 cases** must return the expected
listing among their results, and **every** returned listing must satisfy the
requested complete size label and inclusive price ceiling. No missing expected
item or over-budget/wrong-size result is permitted.

| description | size | max_price | Required listing |
|---|---|---:|---|
| graphic tee | M | 18.00 | lst_002 (S/M) |
| flannel | XL | 22.00 | lst_003 (XL, oversized) |
| jeans | W30 | 38.00 | lst_001 (W30 L30) |
| track jacket | M | 45.00 | lst_004 (M) |
| graphic tee | L | 24.00 | lst_006 (L) |

Compare with the source records, not a model answer. Whole slash-separated
labels count (`M` in `S/M`), parenthetical notes do not change the size, and a
waist-only request can match a waist-plus-inseam record. `L` must never match
`XL`, nor `S` match `US 9`. Each ceiling equals the required listing's price,
so accidentally using a strict `<` comparison fails.

**Why this target:** Budget and size are hard constraints controlled by local
code. A cheaper but unusable item is not a successful recommendation, and a
correct ranking cannot compensate for violating those constraints. Requiring
an expected result prevents an always-empty search from passing vacuously.

---

For Unit 4, preserve these originals. If a criterion cannot be measured, append
an explained revision; do not lower a missed target to fit observed results.
