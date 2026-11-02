# Verification: Structural Defects + Anti-Emptiness + Visual Critique

Every rule below exists because builds failed in one of two ways:
1. **Structural defects** ("floating leaves", "water leaking off the plot", "lanterns in mid-air").
2. **Emptiness / slop** ("it's just a flat 50x50 slab with 12 random lanterns").

Every build must pass **both** automated gates and the **visual render check** before completion:

```bash
python3 scripts/validate.py out.nbt --strict
python3 scripts/quality.py out.nbt
node scripts/render_textured.mjs out.nbt --outdir renders/
```

---

## Gate 1 — Structural Integrity (`scripts/validate.py`)

`validate.py` exits non-zero if any structural defect is detected (`--strict` also promotes warnings to failures).

| Check | Pass condition | Defect prevented |
|---|---|---|
| `nbt.round_trip` | File re-parses; block count matches declared count | Truncated or corrupt `.nbt` |
| `nbt.bounds` | Every block `pos` is inside `size` | Out-of-bounds misalignment |
| `nbt.palette` | `palette[0]` is `minecraft:air`; no duplicate blockstates | Corrupt structure palette |
| `leaves.persistent` | Every leaf state sets `persistent="true"` | Canopies decaying into saplings after paste |
| `trees.floating` | 0 disconnected foliage/wood components floating above ground | Floating leaf clouds or clipped roof tips |
| `trees.soil_on_logs` | 0 soil/grass/moss blocks resting directly atop logs or leaves | Dirt/grass patches sitting on tree canopies |
| `support.plants` | Every flower, grass, fern, petal, sapling rests on valid soil/floor | Floating grass or plants growing on leaves/lanterns |
| `support.hanging` | Hanging lanterns, chains, spore blossoms, weeping vines have solid overhead anchor | Mid-air chains or floor-placed ceiling flora |
| `support.wall_mounted` | Wall signs, wall banners, wall torches have a solid backing block behind `facing` | Detached banners/torches floating in air |
| `fluid.containment` | Water/lava is allowed by default, **provided 0 fluid blocks touch plot edges or have air/non-solid lateral/bottom neighbors** (exempting waterfall drops landing inside a contained basin). Pass `--no-water` only for legacy dry-arena rules. | Water spilling over plot borders or draining through unsealed pond banks |
| `tripwire.absent` | 0 stray tripwire blocks unless `--allow-tripwire` is set | Random floating strings |
| `void.absent` | 0 `structure_void` blocks inside standalone schematics | Invisible collision/paste artifacts |

### How `mckit` prevents structural failures up front
- `Canvas.set()` via `mckit.blocks.default_props()` automatically injects `persistent="true"` on every `*leaves` block.
- `mckit.terrain.carve_pond()` seals all lateral rim banks up to `water_y` and lines the basin floor before filling water.
- `mckit.trees` prunes leaf clouds to 6-connected components anchored to branches *after* checking `canvas.get(x,y,z) == 'air'` (so roofs don't sever outer leaves), and `Canvas.save()` runs `clean_floating_foliage()` + `clean_unsupported_plants()` automatically.

---

## Gate 2 — Anti-Emptiness & Composition (`scripts/quality.py`)

`validate.py` alone will pass an empty 50x50 stone slab! `quality.py` enforces density, vertical relief, composition, and lighting, and writes `renders/quality-heatmap.png`.

| Check | Pass condition | Failure mode prevented |
|---|---|---|
| `footprint.coverage` | `>= 30%` of plot `(x, z)` columns contain detail above base terrain | Flat empty slabs with tiny props in the middle |
| `terrain.relief` | Walkable base-terrain `y` spans `>= 3` vertical levels (`std >= 0.8`) | Pancake-flat terrain with zero elevation change |
| `landmark.prominence` | Peak structure height above median terrain is `>= max(10, min(W, D) * 0.22)` | Low, flat builds with no focal silhouette |
| `cells.no_dead_zones` | On an auto-sized `~10x10` cell grid, `<= 15%` of interior cells have `< 18%` detail density | Forgotten empty corners or barren plazas |
| `surface.variety` | `>= 5` distinct ground/path/water surface materials (`>= 12` distinct non-air block types total) | Monotone single-block floors |
| `lighting.density` | `>= 1.5` light-emitting blocks per `10x10` area, covering `>= 55%` of cells | Pitch-black night renders and mob-spawning dead spots |
| `structure.named_parts` | `.manifest.json` exists with `>= 4` named `Canvas.part(...)` regions | Unstructured random block soup |
| `player.spawn_pad` | Manifest declares a clear 2-block-tall headroom spawn point over solid footing | Players spawning inside walls, trees, or water |
| `palette.coherence` | Top 12 block families account for `>= 60%` of placed blocks | Chaotic rainbow block noise |

Inspect `renders/quality-heatmap.png` whenever a cell fails `cells.no_dead_zones`: red cells pinpoint the exact `(cx, cz)` coordinates that need trees, boulders, stalls, lamps, or pond edges.

---

## Gate 3 — Real-Texture Visual Inspection (`scripts/render_textured.mjs`)

Never deliver a build without inspecting real Minecraft block textures:

```bash
node scripts/render_textured.mjs out.nbt --outdir renders/
```

This renders 8 views using `@mattzh72/lodestone` + Three.js + headless Chromium WebGL:
- `*-hero.png` — Elevated 3/4 beauty angle
- `*-top.png` — Orthographic top-down zone/path audit
- `*-ne.png`, `*-nw.png`, `*-se.png`, `*-sw.png` — All four isometric corners
- `*-eye-spawn.png` — Player first-person view from the spawn pad toward the primary landmark
- `*-night.png` — Dimmed ambient pass highlighting lanterns, froglights, campfires, and neon accents

Open `*-hero.png`, `*-top.png`, `*-eye-spawn.png`, and `*-night.png` with your multimodal file viewer and score all 8 axes in [`critique-rubric.md`](critique-rubric.md). Every axis must score `>= 4/5`. Also verify the renderer emits zero `Untextured block IDs` warnings.

> **Fallback renderer:** `python3 scripts/render3d.py out.nbt` and `python3 scripts/chunk_sheet.py out.nbt` remain available for quick software-rendered checks when Node/Chromium is unavailable, though `render_textured.mjs` is the required standard whenever available.

---

## Live-World Paste Verification (when pasting via FAWE / WorldEdit)

When pasting into a live server (see [`paste-protocol.md`](paste-protocol.md)):
1. **Exact block-count agreement** between the source `.nbt` (`python3 scripts/nbt_query.py out.nbt --counts`) and `//count <block>` in-world for distinctive blocks.
2. **Box arithmetic identity** `void_replaced == sx*sy*sz - non_air_blocks` when pasting without `-a`.
