# Unit 3 build record

Prepared with Codex at James Paek's request on September 23, 2026.
This record describes work as it happens; it does not claim independent
student authorship or a fabricated breakout discussion.

## Milestone 1 — data and starter

Read the first six complete records with `python app.py listings --full -n 6`.
There are 40 listings. Fields: `id`, `title`, `description`, `category`,
`style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.
`style_tags` and `colors` are lists of strings; `price` is numeric; 32 of 40
brands are null. The first six cover jeans, a butterfly tee, a flannel, a
track jacket, corduroy trousers, and a bootleg graphic tee. Size labels include
`S/M`, `XL (oversized)`, `US 8.5`, and `W30 L30`, so a substring size filter
would be wrong. Prices range across the requested budgets; apply the ceiling
before ranking.

Wardrobe items have `id`, `name`, `category`, `colors`, `style_tags`, and nullable
`notes`. The example contains ten pieces; the empty loader returns
`{"items": []}`. The loader removes documentation-only underscore keys.

The untouched starter printed "The planning loop isn't built yet" and used
zero model calls. Raw output and data inspection are in `results/unit3_*.txt`.

## Scope

Unit 3 only: specs, five criteria, three tools, bounded planning loop, session
handoff, CLI, real sample output, and honest AI-use documentation. No Unit 4
MCP migration or formal five-try before/after evaluation is claimed. No optional
stretch feature is claimed.

## Milestones 2–4 — specs, criteria, tools

Committed the Tool Inventory and loop rule before tool implementation, then
committed five acceptance criteria. Criteria 3–5 are disclosed as Codex-drafted
examples; the two supplied criteria retain their original targets.

Implemented local keyword search with complete size labels and inclusive price
ceilings. Real data drove the size rules, including shoe decimals and waist
labels. Both generation tools use the unchanged model adapter. Twelve unit
tests passed. The environment check passed 10/10 with the existing course key.

Before connecting the loop, ran each tool from its own terminal command,
produced three uncached captions for the same input, and ran an empty-wardrobe
sample. The three captions differ but share their opening sentence: variation
alone is not quality. One says "ready to shop", an unsupported availability
implication to evaluate in Unit 4. Lexical search also returned a mesh top
because its description mentions a graphic tee; the actual tee ranks first.
All observations and raw output are retained rather than cleaned up.
