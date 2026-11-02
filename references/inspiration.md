# Research & Web Inspiration Workflow

You are explicitly encouraged to **use web search** before designing a build so your architecture, custom trees, and colour palettes reflect real showcase craftsmanship rather than generic boxes.

## 1. What to Search For
Run 2–3 targeted searches tailored to your chosen theme (each theme card in `references/themes/` includes ready-to-run queries):
- **Showcase spawns & hubs:** `"minecraft <theme> spawn" site:planetminecraft.com OR builtbybit.com OR genmc.app`
- **Custom organic tree silhouettes:** `"minecraft custom <cherry|willow|pine|maple|oak> tree" branches roots canopy`
- **Real-world architectural proportions:** e.g. `"Japanese tahoto pagoda proportions"`, `"taiko-bashi drum bridge garden"`, `"solarpunk glass pavilion concept"`

## 2. How to Distill Search Results into `design.md`
Never copy raw schematics or dump unedited text. Extract **4 concrete design tokens** per reference into the **Inspiration Digest** section of `design.md`:
1. **Silhouette & Proportions:** e.g. *"3-tier pagoda tapers 9→7→5 wide with +2 block roof overhangs and a 4-block sorin finial spire."*
2. **Material Pairing:** e.g. *"Recessed `calcite`/`white_concrete` plaster walls framed by proud `dark_oak_wood` corner columns and `deepslate_tiles` roofs."*
3. **Landscape Integration:** e.g. *"Pagoda sits on a +4y mossy cliff in the NW corner with a waterfall feeding a central lily pond."*
4. **Signature Micro-Detail:** e.g. *"Tōrō stone lanterns (`stone_bricks` + `wall` + `pearlescent_froglight` surrounded by open `cherry_trapdoor`s + `deepslate_tile_slab` cap)."*

## 3. Turning Inspiration into Reusable `mckit` Code
- Check `scripts/mckit/props.py`, `scripts/mckit/trees.py`, and `scripts/mckit/terrain.py` first — many showcase motifs (`place_pagoda`, `place_holo_spire`, `place_bridge`, `place_torii_gate`, `place_campfire_camp`, `place_zen_garden`, `place_tree`, `place_swing`) are already parameterized by theme!
- When inventing a new theme-specific landmark (e.g. a windmill, giant crystal sword, dragon statue, airship dock, samurai gatehouse), write a clean helper function wrapped in `with canvas.part("Landmarks/<Name>"):`, ground all foundations with `_ground_column`, and apply the 3-block depth rule.
