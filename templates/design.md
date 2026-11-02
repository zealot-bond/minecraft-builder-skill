# <Build Title> — `<theme_id>`

> Fill out this concept & zone-plan document **before writing a single block**.
> Every cell in the Zone Map must have a clear role and feature list, and `quality.py`
> will verify the finished `.nbt` against this exact zone grid.

## 1. Brief
- **Dimensions:** `<SX> x <SY> x <SZ>` (e.g. `50 x 40 x 50` standalone island plot)
- **Theme:** `<sakura | samurai | golden_autumn | futuristic | vanilla_plus | fantasy>`
- **Spawn Point & Sightline:** `(sx, sy, sz)` facing `(tx, ty, tz)` — describe what the player sees in the foreground, midground, and background the instant they spawn.
- **Core Player Loop:** Where players spawn, walk, camp, hang out, trade, climb, and explore.

## 2. Inspiration Digest (from Web Search)
Record 3–5 concrete architectural/landscape references gathered via web search:
1. **<Ref 1 — e.g. Japanese Drum Bridge & Koi Sanctuary>:** Palette cue, proportions, signature detail to adapt.
2. **<Ref 2 — e.g. Custom Leaning Cherry Trees>:** Trunk curve, root flare, cloud-cluster canopy + swing branch.
3. **<Ref 3 — e.g. Multi-Tier Pagoda / Spire Silhouette>:** Recessed walls, upturned eaves, finial height.

## 3. Feature Brainstorm (list 12+, select 8–10)
- [x] **Hero Landmark:** ...
- [x] **Water Feature(s):** ...
- [x] **Bridge / Crossing:** ...
- [x] **Custom Tree Species Mix & Swings:** ...
- [x] **Social / Camp Zone:** ...
- [x] **Secondary Architecture (Pavilion / Torii / Dock / Stall):** ...
- [x] **Micro-Details (Lanterns, Benches, Boulders, Petal/Flora Litter):** ...

## 4. Palette Roles
| Semantic Role | Chosen Blocks (including stairs / slabs / walls / trapdoors) |
|---|---|
| Primary Wood | |
| Accent / Structural Timber | |
| Roof & Trim | |
| Stone & Cliff Gradient | |
| Ground & Path Mix | |
| Foliage & Flora | |
| Water & Lighting | |

## 5. Zone Map (1 code per cell; `5x5` for `50x50`, `4x4` for `32x32`)
```text
#   cx=0  cx=1  cx=2  cx=3  cx=4
    .     .     .     .     .      # cz=0 (North)
    .     .     .     .     .      # cz=1
    .     .     .     .     .      # cz=2
    .     .     .     .     .      # cz=3
    .     .     .     .     .      # cz=4 (South)
```

| Code | Zone Name | Planned Structures, Trees & Micro-Details | Target Density |
|---|---|---|---|
| `H` | Hero Landmark | | `>= 2.5` |
| `P` | Pond & Shore | | `>= 1.2` |
| `B` | Bridge | | `>= 1.5` |
| `C` | Campfire Camp | | `>= 1.5` |
| `T` | Swing Trees | | `>= 2.0` |
| `O` | Spawn Approach | | `>= 1.0` |

## 6. Height Profile & Skyline
- **Walkable Clearings:** `y = ...`
- **Pond Water Level:** `y = ...` (basin bed `y = ...`)
- **Hero Outcrop / Mound:** `y = ...`
- **Hero Peak Finial:** `y = ...` (`>= +10` blocks above median ground)

## 7. Layered Build Order
1. `terrain.sculpt_island_plot(...)` — hills, hero outcrop, flat clearings, tapered rocky underside
2. `terrain.carve_pond(...)` + `terrain.build_waterfall(...)` + shoreline boulders
3. `terrain.lay_path(...)` — curved splines linking spawn to every activity zone
4. `props.place_pagoda / place_holo_spire / place_bridge / place_torii_gate / place_gazebo / place_dock`
5. `trees.place_tree(..., with_swing_branch=True)` + `props.place_swing(...)` + bamboo/groves
6. `props.place_campfire_camp / place_market_stall / place_zen_garden / place_spawn_pad`
7. `props.place_street_lamp` + `props.place_bench` + `terrain.scatter_flora`
