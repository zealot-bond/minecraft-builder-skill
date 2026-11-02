# Credits and provenance

This skill was assembled from three sources: two upstream repositories, and the
measured experience of a real spawn rebuild project.

## Upstream repositories (vendored under `vendor/`)

### wzhaoMS/minecraft-builder-skill
<https://github.com/wzhaoMS/minecraft-builder-skill> — MIT

What was taken:

- `vendor/mcb-examples/` — the blueprint examples (ASCII-layer JSON and parametric
  `.mjs`), kept as reference for a declarative build format.
- Design ideas adopted and credited in `SKILL.md` / `references/`:
  - **render a PNG before building, so the agent looks at it** — the contact-sheet and
    `render3d.py` workflow here follows that principle.
  - **verify by reading the world back**, not by trusting the placement command — this
    became the `//count` + box-arithmetic proof in `references/fawe-paste.md`.
  - reversible builds / `mcb undo` informs the "never paste unverified" gate.

`mcb` itself is not vendored (it needs Node + a server transport); install it from the
upstream repo if you want its CLI, MCP server or `/fill`-merging builder. It is the better
tool when you are building *into* a running server interactively; this skill is the better
fit when you are generating a large structure offline and pasting it with FAWE.

### mattzh72/minecraft-builder-skill
<https://github.com/mattzh72/minecraft-builder-skill> — MIT

What was taken:

- `vendor/lodestone-docs/` — the reference documentation, including
  `default-pack-block-states.md` (every legal block-state value), `structure.md`,
  `nbt.md`, `rendering.md` and `recipe-api.md`.
- `vendor/lodestone-scripts/` — `run-build.mjs` and `preview.mjs`.
- `vendor/lodestone-assets/` — the Lodestone viewer and example recipes.

Use that path when you want a **Lodestone JS recipe** and its interactive preview. This
skill's own path (Python palette grid → streaming NBT → FAWE) exists because a 270x270x98
build is 7.1M cells: it needs a flat typed array and a streaming writer, not an object
graph.

## Third-party service

- **Shulkr viewer** <https://www.shulkr.com/en/viewer> — accepts `.litematic`, `.schem`,
  `.nbt`, `.mcstructure` and renders them in the browser. `scripts/shulkr_shot.mjs` drives
  it and screenshots the result. Not affiliated; if their markup changes, the script fails
  loudly rather than producing a blank image.

## Measured experience

Everything in `references/terrain-blend.md`, `references/verification.md`,
`references/pitfalls.md` and the defect table in `README.md` comes from a live Paper
26.3 / FAWE project: a 100x100 arena expanded into a 270x270 spawn on a
`foliumhosting.net` panel, over five rejected iterations.

Concrete numbers quoted in the docs (26-block drop, 68/81 floating canopies, 22 tripwire,
79/80 unsupported banners, 228 corner jumps, 5x4 granite/terracotta parquet at 126/126)
are all measurements from that project, not estimates.

## Licence of vendored material

Upstream files keep their MIT terms; `vendor/LICENSE.mattzh72` is included. The rest of
this repository is MIT — see `LICENSE`.
