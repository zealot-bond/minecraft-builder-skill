# Examples

## 1. Flagship Procedural + Asset-Hybrid Production Spawn (Start Here)

| Example | Theme & Size | What It Demonstrates |
|---|---|---|
| **`06-grand-haven-150x150`** | `vanilla_plus` (`150x96x150`, `243,453` blocks) | Full `5x5` (`30x30`/cell) `design.md` + `ZoneGrid`, `100%` plot terrain (`full_plot=True`), central Spawn Compass Plaza & 8-Pillar Crown Rotunda at `(75, 13, 75)` + 4 Plaza Fountains, `34x28` watertight Emerald Fishing Lake + 5-wide Arched Bridge + Cliff Waterfall + 2 Fishing Piers, 4 Colossal Corner World-Trees (`47–74` blocks tall) + 14 companion oaks + 4 Tree Swings, North Guild Keep + 9 stamped Houses/Manors/Farmhouses + 5 Market Stalls (`Canvas.stamp`), Twin Campfire Camps, 2 Wheat Farm Terraces, 8 Rock Outcrops + 34 small mossy boulders, 46 street lamps, and an unbroken `red_concrete` perimeter border (`terrain.draw_border`). Exports both `.nbt` and Sponge `.schem`. |
| **`07-skyhaven-pvp-100x100`** | `vanilla_plus` (`100x64x100`, `99,558` blocks) | **Box-Inside-Box Spawn + PvP Warzone:** Centered `50x50` Safezone (`x=25..74, z=25..74`) outlined by a walkable `red_concrete` line (`bounds=(25,25,74,74)`), featuring flattened free-roam courtyard, central Spawn Gazebo `(50, 12, 50)`, stamped compact cottages & stalls, Crystal Fishing Pond + Arched Bridge + Pier, **3 Floating Striped Hot Air Balloons** (`props.place_hot_air_balloon`), custom trees + hanging swing, Enchant/Anvil PvP prep station, and campfire nook; surrounded by a flat `100x100` PvP Warzone Ring with flush battle lanes, combat ring, 4 corner Duel/KOTH circles, scattered trees & rocks, and a `blue_concrete` + 3-tall `blue_stained_glass` outer border (`bounds=(0,0,99,99)`). |

Run, gate-check, and texture-render the flagship `150x150` spawn:

```bash
python3 examples/06-grand-haven-150x150/build.py
python3 scripts/validate.py examples/06-grand-haven-150x150/grand-haven-spawn.nbt --strict
python3 scripts/quality.py  examples/06-grand-haven-150x150/grand-haven-spawn.nbt
node scripts/render_textured.mjs examples/06-grand-haven-150x150/grand-haven-spawn.nbt \
        --outdir examples/06-grand-haven-150x150/renders
```

---

## 2. Full-Scale Reference Spawn Builds (Imported from `all-builds.zip`)

Each directory contains both the original Sponge `.schem` schematic and its converted Vanilla Structure `.nbt` file for inspection (`scripts/nbt_query.py`), rendering (`scripts/render_textured.mjs`), or study:

| # | Directory | Dimensions | Non-Air Blocks | Style |
|---|---|---|---|---|
| `01` | `01-economy-smp-spawn` | `78x81x78` | `111,528` | Compact multi-tier Economy SMP hub plaza |
| `02` | `02-japanese-spring-spawn` | `100x58x100` | `52,515` | Sakura-blossom Japanese spring temple & garden island |
| `03` | `03-survival-spawn` | `133x106x151` | `55,090` | Organic hillside survival spawn with paths & overlook |
| `04` | `04-red-kingdom-spawn` | `190x179x190` | `384,198` | Monumental crimson-roofed citadel & kingdom courtyard |
| `05` | `05-trading-post` | `317x176x249` | `707,737` | Expansive medieval harbour & walled trading post |
