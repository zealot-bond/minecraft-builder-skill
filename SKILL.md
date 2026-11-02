---
name: minecraft-builder-skill
description: Design, build, validate, quality-gate, texture-render, and deliver stunning Minecraft Java spawns, hubs, arenas, and schematics. Combines an Art-Director pipeline (auto-picked themes, web-search inspiration, zone-by-zone planning, custom organic trees with swings, watertight ponds, waterfalls, bridges, campsites, and textured Three.js/Lodestone renders) with strict structural and anti-emptiness gates.
---

# Minecraft Builder Skill

**Plan & inspire → zone every chunk → build in layers → validate & quality-gate → texture-render & critique → ship.**

A flat, mostly-empty square of grass or stone is a **rejected failure** even if it has zero floating blocks. Every build produced with this skill must look **instantly stunning** at first glance *and* pass strict physical/structural validation.

---

## Part A — The Art-Director Pipeline (Mandatory for New Builds)

### 1. Pin the brief & auto-pick a vivid theme
If the user says *"create a 50x50 cool spawn"* without naming a style, **do not build generic plain grass**. Auto-pick a bold, cohesive theme from `references/themes/` (or `mckit.get_theme(...)`):
- `sakura` — Cherry-blossom shrine, koi pond, waterfall, vermilion drum bridge, torii gate, Tōrō lanterns, blossom camp
- `samurai` — Feudal mountain keep, dark-tile curved roofs, crimson torii, raked zen rock garden, bamboo grove
- `golden_autumn` — Amber/gold maple valley, mossy stone arch bridge, harvest stalls, roaring campfire camp
- `futuristic` — Neon solarpunk plaza, smooth-quartz & deepslate holo-spire, cyan energy rings, bioluminescent swing trees
- `vanilla_plus` — Overgrown ancient-oak haven, swings, spring waterfall, fishing pier, cozy travellers' camp
- `fantasy` — Enchanted twilight grove, amethyst crystal crags, dark-prismarine shrine, soul-lantern bridge

By default, generate a **self-contained standalone plot** with sculpted organic terrain and a tapered rocky underside so it pastes cleanly into either a void hub world or survival terrain (only use `.mca` terrain blending when the user provides `world/region` files — see `references/legacy-kayleesmp.md`).

### 2. Search the web for real inspiration
Before designing, **use your web search tool** (2–3 targeted queries from `references/inspiration.md` or your theme card) to study showcase builds, custom organic tree silhouettes, bridges, and architectural proportions. Distill 3–5 concrete visual takeaways (silhouette taper, block pairings, landscape framing, signature micro-details) into `design.md`. Never copy raw schematics.

### 3. Write `design.md` and plan EVERY zone cell before placing a block
Copy `templates/design.md` into your output directory as `design.md` and complete it first:
1. **Brainstorm 12–15 features** from `references/feature-catalog.md`, then select **8–10** that fit together naturally. Every spawn (`>= 32x32`) needs:
   - **1 towering off-centre Hero Landmark** (`+14..+26` blocks above ground: 3-tier pagoda, holo-spire, watchtower, bell shrine, ancient world-tree)
   - **1 watertight Water Feature** (koi/lily pond with submerged lights, rock-cradled cliff waterfall, sunken glowing moat)
   - **1 Crossing / Pier** (arched drum/stone bridge with half-slab curve & post lanterns, stepping stones, wooden fishing dock)
   - **Custom Organic Trees in 2–3 distinct silhouettes** (flared roots, curved limbs, airy cloud-cluster canopies — **plus 1–2 trees with hanging wooden chain swings!**)
   - **2–3 Social / Activity Zones** (full campfire camp with cooking spit, log benches & striped A-frame tents; tea pavilion / holo-gazebo; market stalls; zen rock garden)
   - **Framed Spawn Sightline** (compass spawn medallion near one edge facing through an entry gate/torii across water/bridge directly toward the Hero Landmark)
   - **Curved Spline Paths + Micro-Detail** (lanterns every 7–9 blocks, benches, mossy boulders, barrels/crates, wildflower & petal patches)
2. **Draw the ASCII Zone Map** (`5x5` cells of `10x10` blocks on a `50x50` plot; `4x4` cells on a `32x32` plot). **Zero cells may be left empty or "just grass".**

### 4. Build in layers with `scripts/mckit`
Do **not** hand-roll raw flat loops from scratch when `scripts/mckit` provides tested, theme-aware building blocks. Study `examples/05-sakura-pond-camp/build.py` (`50x50`) and `examples/06-neon-futuristic-plaza/build.py` (`32x32`) first.

**Every placed block must live inside a named `with c.part("Category/Name"):` block** (so `quality.py` and the manifest track every building, tree, bridge, pond, camp, and prop):

```python
import os, sys
sys.path.insert(0, '/path/to/minecraft-builder-skill/scripts')
from mckit import Canvas, ZoneGrid, terrain, trees, props, shapes, mix

c = Canvas(50, 40, 50, theme='sakura')
c.zones = ZoneGrid(50, 50, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

# Layer 1 — Organic rolling island, raised hero outcrop, walkable clearings & rocky underside
terrain.sculpt_island_plot(c, base_y=9, hill_amp=2.2,
    mounds=[(13, 12, 11.5, 4.5)],
    flat_zones=[(13, 12, 5.5, 13), (13, 36, 6.0, 9), (26, 42, 4.5, 9)])

# Layer 2 — Watertight koi pond, rock-cradled waterfall & shoreline boulders
pond = terrain.carve_pond(c, center=(25, 22), rx=8.2, rz=6.8, depth=3, water_y=8,
                          stepping_stones=[(22, 18), (25, 17)])
terrain.build_waterfall(c, cliff_x=19, cliff_z=16, top_y=13, water_y=pond['water_y'], dir_dx=1, dir_dz=1)
terrain.place_boulder(c, 17, 17, radius=2.1, mossy=True)

# Layer 3 — Curved Bézier pathways (never rigid 90-degree grid roads)
paths = terrain.lay_path(c, [(26, 44), (26, 35), (25, 29)], width=2.2)

# Layer 4 — Hero landmark, arched bridge, torii/gate, pavilion, dock & custom structures
props.place_pagoda(c, cx=12, cz=11, tiers=3, base_half=4)
props.place_bridge(c, p_start=(25, 9, 29), p_end=(25, 9, 15), arch_height=3.2)
props.place_torii_gate(c, cx=26, cz=35, axis='x', half_span=3, height=7)
props.place_gazebo(c, cx=37, cz=11, radius=3)
props.place_dock(c, start_xz=(33, 21), dir_dx=-1, dir_dz=0, length=5, water_y=pond['water_y'])

# Layer 5 — Campsite, stalls, zen garden & spawn medallion with hero sightline
props.place_campfire_camp(c, cx=13, cz=37, radius=5.2, tents=2)
props.place_market_stall(c, cx=39, cz=40, facing='north')
props.place_zen_garden(c, cx=42, cz=24, rx=3, rz=3)
props.place_spawn_pad(c, cx=26, cz=43, radius=2, look_at=(16, 14, 14))

# Layer 6 — Custom organic trees (with swings!) & bamboo groves
t1 = trees.place_tree(c, x=8, z=25, species='sakura', scale=1.08, with_swing_branch=True)
if t1['swing']:
    props.place_swing(c, t1['swing'], part_name='Props/West Sakura Swing')
trees.place_tree(c, x=31, z=15, species='weeping_willow', scale=0.92)
trees.place_bamboo_clump(c, x=44, z=7, radius=3.4, stalks=14)

# Layer 7 — Lanterns, benches & clustered meadow flora / fallen petals
props.place_street_lamp(c, 22, 39, style='toro')
props.place_bench(c, x=20, z=31, facing='north')
terrain.scatter_flora(c, density=0.28, excluded_cols=paths)

c.save('out.nbt')  # auto-connects fences/walls/panes; writes out.nbt + out.manifest.json
```

Also build **bespoke custom structures** inside `with c.part("Landmarks/..."):` whenever your theme calls for something unique (samurai gatehouse, windmill, dragon statue, crystal portal, airship pier) — following the **3-Block Wall Depth Rule** in `references/design-principles.md`.

### 5. Run BOTH automated gates (non-zero exit = DO NOT SHIP)
```bash
# Gate 1: Structural & physical correctness (0 floating leaves, 0 fluid leaks, persistent leaves, valid supports)
python3 scripts/validate.py out.nbt --strict

# Gate 2: Anti-emptiness & aesthetic richness (0 dead zone cells, terrain relief, hero prominence, variety, lighting, coherence)
python3 scripts/quality.py out.nbt
```
If `quality.py` reports a `DEAD` cell (e.g. `[0,4]=0.16`), inspect `renders/quality-heatmap.png` and populate that cell with purposeful features, groves, boulders, or props until **0 dead cells** remain.

### 6. Render with REAL Minecraft textures & critique with your own eyes
```bash
node scripts/render_textured.mjs out.nbt --outdir renders/
```
This renders 8 full-texture Three.js/Lodestone views (`hero`, `top`, `ne`, `nw`, `se`, `sw`, `eye-spawn`, `night`) and reports any untextured block IDs. (If Node/Chromium is unavailable, fall back to `scripts/render3d.py` + `scripts/chunk_sheet.py` and state so explicitly.)

**View the generated PNGs** (`hero`, `top`, `eye-spawn`, `night`, plus corners) and score all 8 axes in `references/critique-rubric.md` (`1–5`):
- Does `eye-spawn` have an unobstructed, jaw-dropping sightline to the Hero Landmark, or is a tree canopy blocking the view?
- Does `hero` read instantly with foreground, midground water/bridge, and background landmark?
- Are all 4 corners rich in `top`, `ne`, `nw`, `se`, `sw`?
- Does `night` glow warmly with lanterns, campfires, and submerged pond lights?

**Every axis must score `>= 4/5`.** Run up to 3 refinement passes before delivering.

---

## Part B — Engineering & Live-Server Paste Rules

1. **Palette & NBT invariants (`references/structure-nbt.md`, `references/blockstates.md`):**
   - `palette[0]` is always `minecraft:air`.
   - Leaves must carry `persistent: "true"` (`mckit.Canvas` sets this automatically and auto-connects fences, walls, and glass panes).
   - Stream large structures with `scripts/streamnbt.py` (used inside `Canvas.save()`); never materialise millions of Python compound dicts.
2. **Watertight fluids:** Water and lava are encouraged for ponds, waterfalls, fountains, and moats, **provided zero fluid blocks leak**. Every standing fluid block needs solid or waterlogged containment on its bottom and all 4 horizontal sides (`terrain.carve_pond` and `terrain.build_waterfall` enforce this; `validate.py` verifies `fluid.containment`).
3. **Delivering / Pasting with FAWE (`references/fawe-paste.md`):**
   - Generate exact FAWE paste & verification commands with `scripts/paste_commands.py`.
   - When pasting into a live world, never claim a paste succeeded until `//count minecraft:structure_void == 0`, `void_replaced == sx*sy*sz - blocks`, and distinctive block counts match.
   - When blending into an existing `.mca` world or working under server block whitelists, configure `project.json` and follow `references/legacy-kayleesmp.md` + `references/terrain-blend.md`.

---

## Reference Index

| File | Purpose |
|---|---|
| `templates/design.md` | Mandatory pre-build concept, inspiration digest & ASCII zone-grid template |
| `references/design-principles.md` | 3 detail scales, 3-block wall depth, gradients, organic terrain, sightlines |
| `references/feature-catalog.md` | 20+ spawn features with footprints, `mckit` helpers & quality cues |
| `references/themes/*.md` | Curated theme cards (`sakura`, `samurai`, `golden-autumn`, `futuristic`, `vanilla-plus`, `fantasy`) |
| `references/inspiration.md` | Web-search inspiration workflow & distilling design tokens |
| `references/critique-rubric.md` | 8-axis visual rubric (`>= 4/5` required on every axis before shipping) |
| `references/blockstates.md` | Verified `Properties` table & support rules |
| `references/structure-nbt.md` | Exact vanilla `.nbt` byte layout & streaming rules |
| `references/verification.md` | Structural & quality gate pass conditions |
| `references/fawe-paste.md` | FAWE schematic paste anchoring & void arithmetic proof |
| `references/legacy-kayleesmp.md` | Optional `project.json` constraints & `.mca` live-terrain blending |

## Scripts & Toolkit

| Path | Purpose |
|---|---|
| `scripts/mckit/` | Python procedural toolkit: `Canvas`, `ZoneGrid`, `themes`, `palette`, `shapes`, `terrain`, `trees`, `props` |
| `scripts/validate.py` | Gate 1 — structural defects, fluid leaks, persistent leaves, floating foliage, supports |
| `scripts/quality.py` | Gate 2 — anti-emptiness, zone-cell density heatmap, relief, prominence, variety, lighting, coherence |
| `scripts/render_textured.mjs` | Headless real-texture WebGL renderer (Lodestone + Three.js + Chromium) |
| `scripts/render3d.py` | Dependency-light Pillow orthographic voxel renderer (fallback) |
| `scripts/chunk_sheet.py` | Per-tile zoomed contact sheet |
| `scripts/shulkr_shot.mjs` | Optional external Shulkr browser viewer screenshotter |
| `scripts/nbt_query.py` | Summary / histogram / bbox / property inspector for any `.nbt` |
| `scripts/paste_commands.py` | FAWE command emitter with void-identity verification numbers |
| `scripts/read_region.py` | Live `.mca` ground height & `DataVersion` reader |

## Gold-Standard Examples (Read These First)

- `examples/05-sakura-pond-camp/` — **50x50 Sakura Shrine & Pond Camp** (`design.md` + `build.py` + `renders/`): 3-tier pagoda on cliff outcrop, waterfall, koi pond, red drum bridge, fishing dock, torii gate, campfire camp with 2 tents & cooking spit, 2 sakura tree swings, weeping willow, bonsai pine, bamboo grove, zen rock garden.
- `examples/06-neon-futuristic-plaza/` — **32x32 Neon Solarpunk Plaza** (`design.md` + `build.py` + `renders/`): holo energy spire with cyan glass rings & sunken glowing moat, holo-rotunda, bioluminescent swing tree, crystal pods, tech stalls, neon pylons.
- `examples/01..04/` — Engineering micro-lessons (04 is legacy live-terrain blend).
