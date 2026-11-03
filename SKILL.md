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

### 4. Build in layers with `scripts/mckit` + the 371-Asset Library (`assets/`)
Do **not** hand-roll raw flat loops from scratch when `scripts/mckit` provides tested, theme-aware procedural generators **plus 371 tight-cropped hand-crafted assets** in `assets/catalog.json` (`60` oak/blossom trees, `34` assorted colossal trees up to 84 blocks tall, `262` medieval/fantasy houses & cottages, `5` market stalls, and `10` sculpted rock formations). Study `examples/06-grand-haven-150x150/build.py` (`150x150` production spawn) and the curated reference spawns in `examples/01..05/` first.

**Every placed block must live inside a named `with c.part("Category/Name"):` block** (so `quality.py` and the manifest track every building, tree, bridge, pond, camp, and prop):

```python
import os, sys
sys.path.insert(0, '/path/to/minecraft-builder-skill/scripts')
from mckit import Canvas, ZoneGrid, get_asset, terrain, trees, props, shapes, mix

c = Canvas(150, 96, 150, theme='vanilla_plus')
c.zones = ZoneGrid(150, 150, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

# Layer 1 — Sculpted rolling terrain (`full_plot=True` fills 100% corner-to-corner; omit for floating island)
terrain.sculpt_island_plot(c, base_y=11, hill_amp=2.6, full_plot=True,
    mounds=[(18, 18, 18, 4.5), (75, 22, 22, 4.5)],
    flat_zones=[(75, 75, 16, 12), (42, 48, 12, 12)])

# Layer 2 — Watertight fishing pond, rock-cradled waterfall & shoreline boulders
pond = terrain.carve_pond(c, center=(112, 76), rx=17.0, rz=14.0, depth=4, water_y=10)
terrain.build_waterfall(c, cliff_x=114, cliff_z=60, top_y=16, water_y=pond['water_y'], dir_dx=0, dir_dz=1)
terrain.place_boulder(c, 98, 66, radius=2.2, mossy=True)

# Layer 3 — Curved Bézier pathways (never rigid 90-degree grid roads)
paths = terrain.lay_path(c, [(75, 75), (92, 76), (112, 76)], width=2.8)

# Layer 4 — Stamp hand-crafted houses, stalls, colossal corner trees & rocks with 0/90/180/270 rotation
c.stamp(get_asset('houses', 'house_88'), x=42, z=48, rotate=90, part_name='Village/Tavern')
c.stamp(get_asset('stalls', 'stall_01'), x=56, z=60, rotate=180, part_name='Market/BakeryStall')
c.stamp(get_asset('trees_assorted', 'tree_25'), x=19, z=19, sink=2, part_name='Corners/NWWorldTree')
c.stamp(get_asset('rocks', 'rock_03'), x=95, z=64, sink=1, part_name='Pond/ShoreOutcrop')

# Layer 5 — Arched bridge over pond, fishing docks, central spawn pad, campfires & swings
props.place_bridge(c, p_start=(112, 11, 61), p_end=(112, 11, 91), arch_height=4.2, half_width=2)
props.place_dock(c, start_xz=(95, 76), dir_dx=1, dir_dz=0, length=6, water_y=pond['water_y'])
props.place_spawn_pad(c, cx=75, cz=75, radius=4, look_at=(112, 14, 76))
props.place_campfire_camp(c, cx=42, cz=112, radius=6.0, tents=2)
t1 = trees.place_tree(c, x=32, z=76, species='giant_oak', scale=1.15, with_swing_branch=True)
if t1['swing']:
    props.place_swing(c, t1['swing'], part_name='Swings/WestOakSwing')

# Layer 6 — Lanterns, benches, meadow wildflowers & optional perimeter border line
terrain.scatter_flora(c, density=0.24, excluded_cols=paths)
terrain.draw_border(c, block='red_concrete', width=1, raised=1)  # when user requests plot border

c.save('out.nbt', schem_path='out.schem')  # exports Vanilla .nbt + Sponge v2 .schem + .manifest.json
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
| `scripts/mckit/` | Python procedural + schematic toolkit: `Canvas`, `ZoneGrid`, `schem` (`stamp`, `.schem`/`.nbt` IO), `themes`, `palette`, `shapes`, `terrain`, `trees`, `props` |
| `assets/catalog.json` | 371 tight-cropped hand-crafted `.nbt` assets (`trees_oak`, `trees_assorted`, `houses`, `stalls`, `rocks`) ready for `Canvas.stamp(...)` |
| `scripts/validate.py` | Gate 1 — structural defects, fluid leaks, persistent leaves, floating foliage, supports |
| `scripts/quality.py` | Gate 2 — anti-emptiness, zone-cell density heatmap, relief, prominence, variety, lighting, coherence |
| `scripts/render_textured.mjs` | Headless real-texture WebGL renderer (Lodestone + Three.js + Chromium) |
| `scripts/render3d.py` | Dependency-light Pillow orthographic voxel renderer (fallback) |
| `scripts/chunk_sheet.py` | Per-tile zoomed contact sheet |
| `scripts/shulkr_shot.mjs` | Optional external Shulkr browser viewer screenshotter |
| `scripts/nbt_query.py` | Summary / histogram / bbox / property inspector for any `.nbt` |
| `scripts/paste_commands.py` | FAWE command emitter with void-identity verification numbers |
| `scripts/read_region.py` | Live `.mca` ground height & `DataVersion` reader |

## Gold-Standard & Reference Examples (Read These First)

- `examples/06-grand-haven-150x150/` — **Flagship 150x150 Grand Haven Production Spawn** (`design.md` + `build.py` + `.nbt` + `.schem` + `renders/`): central Spawn Rotunda at `(75, 13, 75)`, `34x28` Emerald Fishing Lake with 5-wide Arched Bridge, Cliff Waterfall & 2 Fishing Piers, 4 Colossal Corner World-Trees (`47–74` blocks tall), 4 Tree Swings, Guild Keep + 9 stamped Houses/Manors/Barns + 5 Market Stalls, Twin Campfire Camps, Wheat Farm Terraces, 8 Rock Outcrops + 34 small boulders, and a continuous `red_concrete` perimeter border.
- `examples/01..05/` — **5 Full-Scale Reference Spawns** (`01-economy-smp-spawn`, `02-japanese-spring-spawn`, `03-survival-spawn`, `04-red-kingdom-spawn`, `05-trading-post`) in both `.schem` and `.nbt` formats.
