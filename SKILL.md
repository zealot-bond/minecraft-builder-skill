---
name: minecraft-builder-skill
description: Build Minecraft Java structures as vanilla structure NBT, verify them so no block is misplaced or floating, render them (Shulkr viewer screenshots plus a dependency-free local voxel renderer), and deliver a pastable schematic with FAWE paste commands whose void arithmetic proves the paste was complete. Use for spawns, arenas, terrain blends, decoration passes, or fixing an existing live build.
---

# Minecraft Builder Skill

Build → **verify → look** → paste → prove. The order is not optional: every failure
recorded in this skill came from pasting something that had never been checked.

This skill is the accumulation of a real project that was rejected five times. Each
rejection is encoded here as a hard rule, often with the exact measurement that caught
it. Follow the rules and the same defects do not happen.

---

## The contract (read this before anything else)

**Never invent a number you can measure.** Ground height, water level, an existing
floor pattern, a block's `Properties`, the world's `DataVersion`, the height the terraces
must land on — all of these are readable. Guessing any of them is the root cause of
almost every "it's misaligned / random / ugly" complaint.

**Never claim a build is live because a command was accepted.** A paste is proven by
*exact block-count agreement* plus the *box arithmetic identity* in
`references/fawe-paste.md`. Nothing else counts.

**Never report a render you did not look at.** Generate the images and actually inspect
them. A wide shot hides everything; use the per-chunk contact sheet.

If a check cannot run (stale region file, panel down), say so out loud. A skipped check
is never a pass.

---

## Pipeline

### 0. Pin the geometry first

```
Y0        = world Y of build ly 0            (the //pos1 anchor height)
N, SY     = box width, build height
floor_ly  = the walkable surface, in build ly
```

`box_width >= flat_width + 2 * blend_width`. If the flat area consumes the whole box you
are building a retaining wall, not a blend — fix the width **before** generating.
See `references/terrain-blend.md`.

### 1. Measure the real world

Before building anything that touches existing terrain:

```bash
python3 scripts/read_region.py --dir world/region --box 195 259 270 270 \
        --side-medians --csv ground.csv
python3 scripts/read_region.py --dir world/region --dataversion
```

You get per-side median ground heights and the `DataVersion` for your NBT. Do not
proceed on assumed terrain.

### 2. Generate with a palette grid

```python
G = array('H', bytes(2 * N * SY * N))          # 14 MB for a 270x270x98 box
def I(lx, ly, lz): return ly * N * N + lz * N + lx
```

Every block goes through `pid(name, props)` so states are deduplicated, and
**`palette[0]` must be `air`**. Emit properties explicitly —
`references/blockstates.md` has the verified table.

Write with `scripts/streamnbt.py` (two passes: count, then stream). Never build a list of
block compounds.

### 3. Validate — this is the gate

```bash
python3 scripts/validate.py out.nbt \
        --floor 31 --flat 40 40 229 229 \
        --blend 0 0 269 269 --max-jump 3 \
        --allow-openings 61,135 208,135 135,61 135,208 \
        --strict
```

Non-zero exit means do not continue. It checks: file integrity, palette, bounds, water,
tripwire, plant support, wall-mounted blocks, soil resting on logs, **floating canopy
components**, holes in the flat surface, and surface continuity.

`--allow-openings` is for deliberate openings (ladder shafts). Without it the validator
will correctly fail on those columns.

### 4. Look at it

```bash
python3 scripts/render3d.py out.nbt --views iso,top,low --outdir renders/
python3 scripts/chunk_sheet.py out.nbt --box 85 85 100 100 --tiles 4 --out renders/chunks.png
```

The contact sheet is the one that finds "slop": each tile is 25 blocks, so a floating
canopy or a banner hanging on air is obvious. Inspect the actual PNGs.

### 5. Render on Shulkr (the human-facing screenshot)

```bash
node scripts/shulkr_shot.mjs --nbt out.nbt --out renders/shulkr.png
```

Drives <https://www.shulkr.com/en/viewer>, which accepts `.litematic`, `.schem`, `.nbt`
and `.mcstructure`, uploads the file, waits for the render, and captures a screenshot.
Requires a Chromium binary (`CHROME=/path` to override) and Node 21+.

It prints the page state as well as saving the PNG. **Check that line**: if it contains
`Couldn't load this build in 3D` or shows no dimensions, the render failed and the image
must not be presented as one. The two causes are WebGL being disabled and the file being
handed to the input before the app hydrated — both fixed in the script, both documented in
`references/shulkr-viewer.md`.

### 6. Ship the pastable schematic

The `.nbt` **is** the schematic: upload it to
`plugins/FastAsyncWorldEdit/schematics/` and `//schem load <name>`.

```bash
python3 scripts/paste_commands.py --pos 195 42 259 --size 270 98 270 \
        --schem macetopia-v6 --blocks 2126796 \
        --count minecraft:polished_granite --count minecraft:terracotta
```

It prints the exact `N blocks have been replaced.` value you must see. Run the three
emitted command lists as **separate** console sessions.

### 7. Prove the paste

- `//count minecraft:structure_void` → **0**
- the void replacement count == `sx*sy*sz - blocks`
- `//count <distinctive block>` == the count in your NBT, exactly

Only then is it done.

---

## The rules that keep it from looking wrong

**Flat means flat.** Everything the player walks on is one Y. Variation goes outside, in
at most 2-3 broad steps.

**Risers are dirt, not stone.** Soil body deeper than the tallest riser, or grey bands
appear and it reads as a cliff.

**Corners need one continuous rim loop.** Per-side heights meeting at a corner is the
"overlapping corners" defect. See `references/terrain-blend.md`.

**Trees are grounded, on soil.** A tree floats if its trunk does not reach the floor; a
tree on bare stone/glass looks wrong, so give it a 3x3 pad. Vary the model, and never put
two of the same model next to each other.

**Reproduce existing floor designs exactly.** Fit the rule from the source and verify it
at 100% on a clean area before applying it elsewhere (a real one was a 5x4
granite/terracotta basket-weave: `((x//5)+(z//4))%2`).

**Decoration is intentional or absent.** No random small blocks, no tripwire, no banners
without a wall behind them, no "something interesting" scattered by hash. If the user
asks for fewer objects, remove them *all* rather than thinning them.

---

## References

| File | What it answers |
|---|---|
| `references/blockstates.md` | the verified `Properties` table; which blocks need support |
| `references/structure-nbt.md` | exact byte layout; the compound-in-list bug; palette rules |
| `references/fawe-paste.md` | paste anchoring, destructive void, the arithmetic proof |
| `references/region-read.md` | reading `.mca`: section order, water, cave artefacts |
| `references/terrain-blend.md` | five failed blends and the one that worked |
| `references/verification.md` | the pass/fail table and what "verified" may mean |
| `references/shulkr-viewer.md` | Shulkr upload/screenshot; the WebGL and hydration traps |
| `references/pitfalls.md` | shell/browser/panel traps that fake success |
| `vendor/lodestone-docs/` | every legal block-state value; Lodestone recipe/render API |
| `vendor/mcb-examples/` | upstream `mcb` blueprints (ASCII layers) for reference |

## Scripts

| Script | Purpose |
|---|---|
| `streamnbt.py` | streaming structure-NBT writer (no compound objects) |
| `validate.py` | the gate — all structural checks, non-zero exit on failure |
| `nbt_query.py` | summary/counts/bbox/props/histogram of any structure NBT |
| `render3d.py` | dependency-free voxel renderer (iso / top / low / corner) |
| `chunk_sheet.py` | NxN contact sheet for spotting slop |
| `read_region.py` | ground truth, water, DataVersion from live `.mca` |
| `paste_commands.py` | FAWE command lists + the expected void arithmetic |
| `shulkr_shot.mjs` | upload to Shulkr viewer and screenshot the render |
| `trees.py` | five distinct tree models, all grounded and pruned |

## Examples

- `examples/01-flat-plaza/` — minimal: a flat plaza, a border ring, nothing else.
- `examples/02-terrain-blend/` — the continuous rim loop + flat lawn + 2-3 big steps.
- `examples/03-parquet-ring/` — reproduce an existing floor design and continue it.
- `examples/04-full-spawn/` — the complete generator this skill was distilled from.

Run any of them with `python3 examples/<name>/build.py`; each writes an `.nbt` and can be
validated and rendered with the scripts above.

## Credits

Builds on `wzhaoMS/minecraft-builder-skill` (the `mcb` CLI: preview PNGs, verify-after-build,
undo) and `mattzh72/minecraft-builder-skill` (Lodestone recipes and the block-state docs).
See `CREDITS.md`. Everything under `vendor/` is theirs, under their licences.
