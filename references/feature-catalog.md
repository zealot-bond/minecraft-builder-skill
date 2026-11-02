# Spawn Feature Catalog (Brainstorm Menu)

When designing a spawn or hub, brainstorm **12–15 candidate features** from this menu and select **8–10** that fit your theme and plot size so every zone cell feels purposeful and alive.

| Category | Feature | Typical Footprint | `mckit` Helper / Recipe | What Makes It Stunning (vs. Lazy) |
|---|---|---|---|---|
| **Hero Landmarks** | **3-Tier Pagoda / Shrine** | `11x11` (`+20y`) | `props.place_pagoda` | Stepped stone plinth, recessed white walls, proud dark timber pillars, upturned eaves, 8 hanging corner lanterns, finial spire |
| | **Holo Energy Spire** | `13x13` (`+20y`) | `props.place_holo_spire` | Sunken glowing water moat, 4 curved quartz buttress fins, 2 suspended stained-glass rings, sea-lantern core |
| | **Ancient World-Tree** | `15x15` (`+18y`) | `trees.place_tree(..., scale=1.35)` | Thick twisted roots, lantern canopy, 2 hanging swings, shrine tucked between roots |
| | **Clock / Bell Watchtower** | `9x9` (`+18y`) | Custom `Canvas` | Stone-to-andesite vertical gradient, recessed timber gallery, hanging bell, steep gabled roof |
| **Water Features** | **Koi / Lily Pond** | `14x18` (`depth 3`) | `terrain.carve_pond` | Irregular noise shoreline, watertight rim, submerged froglights, lily pads, sugar-cane reeds, stepping stones |
| | **Cliff Waterfall** | `5x5` (`drop 4–7`) | `terrain.build_waterfall` | Cradled on 3 sides by mossy boulders, pouring from hero outcrop directly into pond |
| | **Sunken Glowing Moat** | Ring `r=5..7` | `props.place_holo_spire` | Flush quartz retaining rim, prismarine + sea-lantern bed under calm source water |
| **Crossings & Piers** | **Arched Drum Bridge** | `5x15` (`arch +3`) | `props.place_bridge` | Smooth half-slab parabolic curve, submerged piers, dark-oak railings, 6 post lanterns |
| | **Stepping-Stone Ford** | `2x2` stones | `carve_pond(stepping_stones=...)` | Waterlogged top slabs & mossy stones skimming water surface |
| | **Wooden Fishing Pier** | `3x6` over pond | `props.place_dock` | Log pilings anchored to pond floor, slab deck, fence posts, tip lantern & fish barrels |
| **Social & Camp** | **Adventurer Campfire Camp** | `11x11` clearing | `props.place_campfire_camp` | Stone hearth, lit campfire with timber cooking spit + chain, stripped-log benches, 2 striped wool A-frame tents with chests/barrels inside |
| | **Open-Air Tea Pavilion** | `8x8` (`+9y`) | `props.place_gazebo` | Raised plinth, 4 corner columns, fence balustrades, layered overhang roof, hanging chandelier |
| | **Market / Blossom Stalls** | `5x4` each | `props.place_market_stall` | Upside-down stair counter, striped wool awning, barrels, chest, hanging lantern & candles |
| **Gates & Pads** | **Vermilion Torii / Entry Arch** | `9x3` (`+8y`) | `props.place_torii_gate` | Grounded stone pedestals, twin columns, tie-beam (`nuki`), upturned double lintel, twin lanterns |
| | **Compass Spawn Medallion** | `5x5` flush | `props.place_spawn_pad` | Chiseled stone / lodestone centre, 4 cardinal froglights/sea-lanterns, clear sightline |
| **Nature & Gardens** | **Swing Trees** | `11x11` canopy | `trees.place_tree(with_swing_branch=True)` + `props.place_swing` | Sturdy horizontal crossbar limb at `y+7`, dual iron chains, 5-wide slab bench, under-seat lantern |
| | **Weeping Waterside Willow** | `10x10` canopy | `trees.place_tree(species='weeping_willow')` | Leaning trunk over pond bank, 4–5 block draping leaf curtains |
| | **Windswept Bonsai Pine** | `9x9` canopy | `trees.place_tree(species='japanese_pine')` | S-curved dark trunk, flat horizontal spruce/dark-oak cloud pads |
| | **Bamboo Sanctuary** | `8x8` grove | `trees.place_bamboo_clump` | 12–16 multi-height stalks (`small`/`large` leaves) on podzol with mossy boulders & Tōrō lantern |
| | **Zen Raked Rock Garden** | `7x7` framed | `props.place_zen_garden` | Dark-oak border, alternating `calcite`/`gravel` raked waves, off-centre mossy boulder cluster, Tōrō lantern |
| **Micro-Details** | **Lantern Avenue** | `1x1` (`+4y`) | `props.place_street_lamp` | Tōrō stone lanterns, hanging timber lamp posts, or sci-fi neon end-rod pylons every 7–9 blocks along paths |
| | **Scenic Overlook Benches** | `5x1` | `props.place_bench` | 3 stair seats + upturned trapdoor armrests facing the pond, fire, or vista |
| | **Mossy Crag Boulders & Flora** | `3x3`–`5x5` | `terrain.place_boulder` + `scatter_flora` | Noise-warped stone/andesite/moss blobs tucked into hillsides + clustered `pink_petals`, tulips, ferns |
