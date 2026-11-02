# Theme Card: `sakura` — Sakura Shrine & Pond

## Vibe & Atmosphere
Serene Japanese spring sanctuary: leaning pink cherry blossoms, vermilion drum bridges and torii gates, lily-covered koi ponds fed by mossy crag waterfalls, raked gravel gardens, and warm Tōrō stone lanterns.

## Palette & Gradient Roles (`mckit.get_theme('sakura')`)
- **Primary Wood:** `cherry` (`cherry_wood`, `cherry_planks`, `cherry_stairs`, `cherry_slab`, `cherry_trapdoor`, `cherry_fence`)
- **Structural Timber:** `dark_oak` (`dark_oak_wood`, `stripped_dark_oak_log`, `dark_oak_fence`, `dark_oak_slab`)
- **Lacquer Accent (Bridge & Torii):** `mangrove` (`mangrove_wood`, `mangrove_planks`, `mangrove_slab`, `mangrove_stairs`, `mangrove_fence`)
- **Pagoda Roofs & Trim:** `deepslate_tiles` (`block`, `stairs`, `slab`) with `mangrove_slab` upturned eaves; recessed `white_concrete` / `calcite` walls
- **Cliff & Stone Gradient:** `deepslate` → `tuff` → `andesite` → `stone` → `mossy_cobblestone`; `stone_bricks` plinths & curved paths
- **Canopies & Flora:** `cherry_leaves` (80%) + `flowering_azalea_leaves` (20%), `bamboo`, `pink_petals`, `pink_tulip`, `white_tulip`, `allium`, `fern`, `lily_pad`, `sugar_cane`
- **Lighting & Water:** `lantern`, `pearlescent_froglight` (submerged pond glow & Tōrō cores), `campfire`

## Signature Landmarks & Features
1. **3-Tier Pagoda Shrine** (`props.place_pagoda`) on a raised NW rocky mound with a cascading **Waterfall** (`terrain.build_waterfall`).
2. **Vermilion Drum Bridge** (`props.place_bridge`) arching over a **Koi Pond** (`terrain.carve_pond`) with stepping stones & fishing pier (`props.place_dock`).
3. **Custom Leaning Sakura Trees** (`trees.place_tree(species='sakura', with_swing_branch=True)`) with 5-wide wooden chain **Swings** (`props.place_swing`) and petal litter.
4. **Vermilion Torii Gate** (`props.place_torii_gate`), **Tea Pavilion** (`props.place_gazebo`), **Zen Rock Garden** (`props.place_zen_garden`), **Bamboo Grove** (`trees.place_bamboo_clump`), and **Blossom Campfire Camp** (`props.place_campfire_camp`).

## Web Inspiration Queries
- `minecraft japanese sakura spawn koi pond drum bridge build`
- `minecraft custom cherry blossom tree tutorial roots branches`
- `minecraft japanese pagoda shrine stone lantern detail`
