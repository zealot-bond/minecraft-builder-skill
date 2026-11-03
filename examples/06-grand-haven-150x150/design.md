# Grand Haven Spawn (`150x150` Production Server Hub) — `vanilla_plus`

## 1. Brief
- **Dimensions:** `150 x 96 x 150` (`22,500` ground columns, 100% full-plot coverage with continuous `red_concrete` perimeter border line)
- **Theme:** `vanilla_plus` (*Overgrown Meadow & Medieval Haven*), combining `mckit` procedural terrain/water/bridges/rotunda with hand-crafted trees, homes, market stalls, and rock assets extracted from `all-builds.zip`
- **Spawn Point & Sightline:** Central Spawn Rotunda at `(75, 13, 75)` facing `(112, 14, 76)` — players spawn inside an open-arched 8-pillar Crown Rotunda on an inlaid 21×21 Compass Medallion, looking straight down the East Lantern Promenade toward the **Emerald Fishing Pond** and its **5-wide Arched Bridge**, with **Massive Corner Trees (47–74 blocks tall)** framing the skyline in every direction.
- **Exports:** Both `grand-haven-spawn.nbt` (Vanilla Structure) and `grand-haven-spawn.schem` (WorldEdit / FAWE Sponge v2 schematic).

## 2. Zone Map (`5x5` Grid of `30x30` Districts = `150x150`)
```text
#   cx=0   cx=1   cx=2   cx=3   cx=4
    N      G      K      W      E      # cz=0 (z=0..29)   NW Giant Tree | West Keep Manor | North Guild Keep | Waterfall Ridge | NE Giant Tree
    V      M      A      O      P      # cz=1 (z=30..59)  West Cottages | Market Square   | North Avenue     | Overlook Gazebo | North Cove
    V      M      S      B      P      # cz=2 (z=60..89)  Artisan Homes | Bazaar Stalls   | CENTRAL SPAWN    | FISHING BRIDGE  | East Lake Shore
    T      C      R      L      H      # cz=3 (z=90..119) Swing Grove   | Campfire Camp   | South Promenade  | South Pier Cove | Angler Cottage
    Q      C      F      F      Z      # cz=4 (z=120..149)SW Giant Tree | Camp Overlook   | Homestead Farms  | Farmhouse Barn  | SE Giant Tree
```

| Code | District (`30x30`) | Key Landmarks, `all-builds.zip` Assets & Micro-Details |
|---|---|---|
| `S` | **Central Spawn Plaza (`[2,2]`)** | Open 8-pillar Vaulted Crown Rotunda (`y=12..35`), 21×21 Compass Medallion, 4 cardinal Torii/Timber Entry Arches, 4 NPC/Crate Pavilions, corner fountains |
| `B, P, L` | **Emerald Fishing Lake & Bridge (`[3,2],[4,1],[4,2],[3,3]`)** | `34x28` watertight Fishing Pond (`water_y=10`), 5-wide Arched Bridge spanning West-to-East over the pond, 2 wooden Angler's Fishing Piers with barrels & lanterns, stepping stones, reeds, lily pads |
| `W, O` | **Waterfall Crag & Cliff Gazebo (`[3,0],[3,1]`)** | Mossy cliff Waterfall pouring from `y=18` into the lake, sculpted rock assets (`rock_06..09`), Overlook Gazebo & Zen Rock Garden |
| `K, G, A` | **North Guild Keep & Citadel (`[2,0],[1,0],[2,1]`)** | Elevated `y=17` fortress plateau, 3-Tier Grand Guild Keep (`+32y`), Diorite/Prismarine Guild Manors (`house_193`, `house_205`), Stone Watchtower (`house_157`), grand ceremonial staircase |
| `V, M` | **Artisan Village & Market (`[0,1],[1,1],[0,2],[1,2]`)** | 5 Medieval Townhouses & Timber Inns (`house_61`, `house_73`, `house_85`, `house_97`, `house_133`), all 5 hand-built Market Stalls (`stall_01..05`), village well, benches, flowerbeds |
| `C, T` | **Campfire Clearing & Swing Grove (`[0,3],[1,3],[1,4]`)** | Twin roaring Campfire Camps (3 striped A-frame tents, cooking spits, log benches), custom Giant Oak & Sakura Swing Trees with 4 wooden chain swings |
| `F, R, H` | **Homestead Farm & Angler's Cove (`[2,3],[2,4],[3,4],[4,3]`)** | Thatched Farmhouse & Barn (`house_217`, `house_229`), terraced golden wheat/hay/berry fields, lakeside Angler's Cottage (`house_145`), fishmonger stalls |
| `N, E, Q, Z` | **4 Massive Corner Sanctuaries (`[0,0],[4,0],[0,4],[4,4]`)** | Colossal 47–74 block custom trees (`tree_05`, `tree_06`, `tree_12`, `oak_01`, `oak_25`, `oak_37`, `oak_49`), companion custom oaks, hand-sculpted rocks & mossy boulders |
| **Border** | **Full `150x150` Red Perimeter Line** | Continuous terrain-conforming `red_concrete` border around `x=0`, `x=149`, `z=0`, `z=149` |
