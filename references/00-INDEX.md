# Reference index

Read in this order depending on what you are doing.

## Before you place a single block

1. **`terrain-blend.md`** — decide the box width, measure the ground, understand why
   `box_width > flat_width`. Skipping this is how you build a retaining wall.
2. **`structure-nbt.md`** — the file format and the two bugs that corrupt it.
3. **`blockstates.md`** — the properties you must emit, and what decays or mis-faces if
   you do not.

## While generating

4. **`terrain-blend.md`** steps 2-6 — the continuous rim loop, the height field, the flat
   lawn + big steps, and the continuity assertion.

## Before you paste

5. **`verification.md`** — the full pass/fail table; run `scripts/validate.py`.
6. **Look at the render** (`render3d.py`, `chunk_sheet.py`, `shulkr_shot.mjs`). A build
   that has not been looked at is a guess.

## When pasting

7. **`fawe-paste.md`** — anchoring, the destructive void, and the box-arithmetic proof.
8. **`region-read.md`** — reading the result back correctly (section order, water,
   stale files).

## When something is wrong

9. **`pitfalls.md`** — the tooling traps that make you believe work succeeded when it did
   not. Check here before re-generating anything.

## Vendored upstream

- `vendor/lodestone-docs/default-pack-block-states.md` — every legal block-state value.
  Grep it before choosing a property value.
- `vendor/lodestone-docs/recipe-api.md`, `structure.md`, `nbt.md`, `rendering.md` — the
  Lodestone JS recipe path.
- `vendor/lodestone-scripts/` — `run-build.mjs`, `preview.mjs`.
- `vendor/mcb-examples/` — ASCII-layer blueprints from the `mcb` CLI.
