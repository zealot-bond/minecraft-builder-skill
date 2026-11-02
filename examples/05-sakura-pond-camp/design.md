# Hanami Sanctuary — Sakura Pond & Shrine Camp (`sakura`)

## 1. Brief
- **Dimensions:** `50 x 38 x 50` standalone island plot (walkable ground `y = 8..14`, pagoda finial `y = 33`).
- **Spawn Point:** `(26, 10, 42)` facing North-Northwest toward `(15, 15, 14)` so the player immediately sees the **Vermilion Torii Gate → Arched Drum Bridge → Koi Pond & Waterfall → 3-Tier Pagoda Shrine** layered in depth.
- **Purpose:** Server spawn / survival hub clearing where players spawn, explore a koi pond, hang out on tree swings, camp around a roaring fire, trade at a blossom stall, and climb up to the shrine.

## 2. Inspiration Digest
1. **Japanese Hanami Shrine Spawns (BuiltByBit / PlanetMinecraft):** Off-centre multi-tier pagoda elevated on a craggy rock outcrop so its silhouette commands the skyline without blocking the central pond.
2. **Traditional Drum Bridge (*Taiko-bashi*) & *Tōrō* Lanterns:** Steeply arched mangrove/crimson bridge deck in half-slab increments with dark-oak balustrades and stone garden lanterns reflecting over lily-pad water.
3. **Custom Organic Cherry Trees:** Leaning curved `cherry_wood` trunks with flared surface roots, pancake cloud clusters (`cherry_leaves` + `flowering_azalea_leaves` with 22% subtracted air pockets), hanging lanterns, fallen `pink_petals` litter, and sturdy horizontal limbs supporting 5-wide chain swings.
4. **Cozy RPG Campsites:** Gravel-and-podzol hearth clearing with a timber cooking spit over a lit campfire, stripped-log benches, and striped wool A-frame tents stocked with barrels and chests.

## 3. Palette (`sakura` theme card)
| Role | Blocks |
|---|---|
| Primary Timber | `cherry_wood`, `cherry_planks`, `cherry_stairs`, `cherry_slab`, `cherry_trapdoor`, `cherry_fence` |
| Structural Dark Timber | `dark_oak_wood`, `dark_oak_fence`, `dark_oak_slab`, `stripped_dark_oak_log` |
| Lacquer Accent (Bridge & Torii) | `mangrove_wood`, `mangrove_planks`, `mangrove_slab`, `mangrove_stairs`, `mangrove_fence` |
| Pagoda Walls & Roofs | Recessed `white_concrete` / `calcite` walls; `deepslate_tiles` roof tiers with `mangrove_slab` upturned eaves |
| Stone & Cliffs | `deepslate` → `tuff` → `andesite` → `stone` → `mossy_cobblestone`; `stone_bricks` plinths & paths |
| Foliage & Ground | `cherry_leaves`, `flowering_azalea_leaves`, `azalea_leaves`, `spruce_leaves`, `bamboo`, `pink_petals`, `moss_block`, `podzol` |
| Water & Lighting | `water` koi basin, `pearlescent_froglight` submerged & lantern cores, `lantern`, `campfire` |

## 4. Zone Map (`5 x 5` grid, each cell = `10 x 10` blocks, North at top)
```text
#   cx=0  cx=1  cx=2  cx=3  cx=4
    S     H     W     G     B      # cz=0 (z 0..9)   Shrine Hill, Waterfall, Gazebo, Bamboo
    H     H     P     P     G      # cz=1 (z 10..19) Pagoda Shrine, North Pond, Pavilion
    T     P     D     P     Z      # cz=2 (z 20..29) Swing Tree W, Pond, Drum Bridge, Zen Garden
    C     C     R     T     M      # cz=3 (z 30..39) Campfire Camp, Torii Gate, Swing Tree E, Market
    C     F     O     F     M      # cz=4 (z 40..49) Camp Edge, Flower Meadow, Spawn Pad, Stall Plaza
```

| Code | Zone Role | Key Features & Micro-Details |
|---|---|---|
| `H` | Hero Shrine Outcrop | Raised `y=13` rock cliff, 3-tier Pagoda Shrine (`y=33`), stone stairs, corner lanterns |
| `W` | Waterfall Crag | Mossy boulders, rock-cradled waterfall cascading from `y=13` into the North pond |
| `P` | Koi Pond & Pier | Watertight `y=8` koi basin, submerged froglights, lily pads, reeds, stepping stones, dock |
| `D` | Red Drum Bridge | Arched mangrove/dark-oak bridge spanning the pond waist with 6 post lanterns |
| `G` | Tea Pavilion | Open-air timber pavilion overlooking the pond + weeping willow dipping toward the shore |
| `B` | Bamboo Sanctuary | Multi-height bamboo grove on podzol, mossy boulders, Tōrō stone lantern |
| `Z` | Zen Rock Garden | Dark-oak framed raked `calcite`/`gravel` garden, meditation stones, bonsai pine |
| `C` | Campfire Camp | Roaring campfire with cooking spit, stripped-log benches, 2 striped tents, barrels |
| `T` | Swing Sakura Trees | Two giant leaning custom cherry trees with horizontal swing branches & 5-wide chain swings |
| `R` | Torii Approach | Vermilion Torii gate framing the bridge & pagoda, flanked by Tōrō lanterns |
| `O` | Spawn Medallion | Chiseled stone & froglight compass pad at `(26, 42)` facing the Torii & Pagoda |
| `M` | Blossom Market | Striped market stall, wooden benches, crates, cherry & azalea trees |
| `S/F`| Meadow & Rim | Sculpted sakura groves, mossy boulders, fallen `pink_petals` and tulip clusters |

## 5. Build Order
1. **Terrain & Underside:** Sculpt organic `50x50` island with raised NW outcrop (`mound` at `(13, 12)`), flat clearings for Spawn, Camp, Pavilion & Shrine, and tapered rocky underside.
2. **Water:** Carve watertight Koi Pond (`(25, 23)`) + rock-cradled Waterfall from the NW shrine cliff (`(19, 14)`).
3. **Paths:** Curved `stone_bricks`/moss/gravel paths linking Spawn → Torii → Camp, Spawn → Market → Zen → Pavilion, and Bridge → Shrine stairs.
4. **Hero & Architecture:** 3-Tier Pagoda Shrine, Vermilion Drum Bridge, Torii Gate, Tea Pavilion, Fishing Dock, Zen Rock Garden.
5. **Custom Trees & Swings:** Giant Sakura trees (2 with chain swings!), Weeping Willow by the pond, windswept Bonsai Pine, Azalea bushes, Bamboo grove.
6. **Campsite, Props & Micro-Detail:** Full Campfire Camp (2 tents, benches, spit), Market Stall, Tōrō lanterns, park benches, shoreline boulders, and wildflower / `pink_petals` scatter.
