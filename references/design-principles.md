# Design Principles: What Makes a Minecraft Spawn Look Stunning

An empty flat square passes every crash/syntax test and fails every human eye test.
Follow these **six checkable craft rules** on every build.

---

## 1. Three Scales of Detail in Every Zone
Every cell on your zone map needs geometry at three scales:
1. **Macro (Silhouette, 12–28 blocks):** Off-centre hero landmark (pagoda, spire, bell tower, ancient world-tree, cliff waterfall) that reads clearly from across the plot.
2. **Meso (Zones & Structures, 5–12 blocks):** Arched bridges, pavilions, A-frame camp tents, market stalls, fishing piers, custom leaning trees with swings.
3. **Micro (1–3 blocks):** Tōrō stone lanterns, benches with trapdoor armrests, barrels & crates, mossy boulders, lily pads, sugar cane, hanging chains, and clustered `pink_petals` / ferns.

## 2. The 3-Block Wall Depth Rule
Never place a flat wall longer than 5 blocks on a single plane:
- **Outer layer (`+1`):** Proud corner timber columns (`*_wood`), roof overhangs (`+2` blocks past walls with upturned corner slabs/stairs), hanging lanterns, window sills.
- **Middle layer (`0`):** Timber crossbeams, stair arches, trapdoor shutters.
- **Inner layer (`-1`):** Recessed light plaster (`white_concrete`/`calcite`) or tinted glass panes (`*_stained_glass_pane`).

## 3. Organic Terrain — Break the Grid
Unless a legacy `project.json` explicitly asks for a flat arena floor:
- **Rolling relief:** Ground height should vary naturally across the plot (`std >= 1.0` blocks), rising into a rocky outcrop (`+4..+6` blocks) under the hero landmark and dipping gently into a pond basin (`-1..-3` blocks).
- **Curved splines, never 90° grid roads:** Run paths along 3-point Bézier curves (`terrain.lay_path`) with weathered edge blocks (`gravel`, `andesite`, `mossy_stone_bricks`, scattered `stone_button` pebbles).
- **Sculpted standalone rim & underside:** Taper the outer 2 blocks of the plot with organic noise and build a craggy stone/tuff/deepslate underside (`underside=True`) so the schematic looks like a floating sanctuary island in void worlds *and* settles cleanly into survival terrain.

## 4. Gradients & Material Mixes (Never Single-Block Fills)
- **Vertical cliff gradients:** Dark/heavy stone at the base (`deepslate` → `tuff` → `andesite` → `stone` → `mossy_cobblestone`), capped by `coarse_dirt` and `grass_block` / `moss_block`.
- **Weighted surface mixes (`mckit.mix`):** A stone path is never 100% `stone_bricks`; mix `stone_bricks (50%) + mossy_stone_bricks (20%) + cracked_stone_bricks (15%) + andesite (15%)`. No single surface block may exceed `55%` of the plot (`quality.py` enforces this).

## 5. Custom Organic Trees (Never Lollipops)
- **Flared roots:** Anchor trunks with 3–5 asymmetric roots stepping down to `ground_y` surrounded by `podzol` and `rooted_dirt` (never soil *on top* of logs).
- **Curved, tapering 6-connected limbs:** Lean cherry and willow trees toward water or over paths; step thickness from `2x2` base → `1x1` limbs.
- **Cloud-cluster canopies ("Cluster & Subtract"):** Build flattened pancake leaf blobs (`rx > ry`) around branch tips, subtract `20–25%` of outer leaves so light filters through, mix 2–3 complementary leaf blocks (`cherry_leaves` + `flowering_azalea_leaves`), and hang chains + lanterns or a 5-wide wooden swing from a sturdy horizontal limb.

## 6. Framed Sightlines & Player Ergonomics
- **Spawn sightline:** Place the spawn medallion near one edge (`cz ≈ 0.82 * sz`) facing across water/bridge toward the off-centre hero landmark (`rule of thirds`), framed in the foreground by a Torii gate or archway and flanking trees.
- **Walkability:** Keep clearings flat where structures sit (`flat_zones`), use half-slab curves on arched bridges so players walk across without jumping, and place at least 1 light source per 40–60 ground columns.
