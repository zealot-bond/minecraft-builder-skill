# Examples

## Gold-Standard Showcase Spawns (Start Here)

| Example | Theme & Size | What It Demonstrates |
|---|---|---|
| **`05-sakura-pond-camp`** | `sakura` (`50x40x50`) | Full `design.md` + `ZoneGrid` + sculpted island & rocky underside, 3-tier Pagoda Shrine on cliff outcrop, rock-cradled waterfall, watertight Koi Pond with lily pads & submerged lights, Vermilion Drum Bridge, fishing pier, Torii Gate, Campfire Camp (2 striped tents, cooking spit, log benches), 2 custom Sakura Trees with hanging wooden Swings, Weeping Willow, Bonsai Pine, Bamboo Grove, Zen Rock Garden, Blossom Stalls, Tōrō lanterns & petal scatter |
| **`06-neon-futuristic-plaza`** | `futuristic` (`32x34x32`) | Theme generality using the same `mckit` toolkit: Holo Energy Spire with 4 quartz buttress fins, 2 cyan glass holo-rings & sunken glowing water moat, Holo-Rotunda pavilion, bioluminescent Neon Swing Tree, crystal pods, tech stalls & neon pylons |

Run, gate-check, and texture-render either showcase example:

```bash
python3 examples/05-sakura-pond-camp/build.py
python3 scripts/validate.py examples/05-sakura-pond-camp/sakura-pond-camp.nbt --strict
python3 scripts/quality.py  examples/05-sakura-pond-camp/sakura-pond-camp.nbt
node scripts/render_textured.mjs examples/05-sakura-pond-camp/sakura-pond-camp.nbt \
        --outdir examples/05-sakura-pond-camp/renders
```

---

## Engineering Micro-Lessons (Low-Level Mechanics Only)

> **Note:** `01–03` teach individual low-level mechanics (raw NBT grid, rim loop, floor fitting) and intentionally fail `quality.py` because they have no landmarks, zones, or detail. Never imitate `01` for a user build!

| # | Focus | Standalone? |
|---|---|---|
| `01-flat-plaza` | Minimal `array('H')` palette grid & `streamnbt` write (intentionally fails `quality.py`) | yes |
| `02-terrain-blend` | Continuous perimeter rim loop + stepped `.mca` terrain blend | yes (synthetic ground) |
| `03-parquet-ring` | Fitting and continuing an existing floor pattern | yes |
| `04-full-spawn` | Legacy v1 270x270 live-world blend generator (`kayleesmp`) | no — requires external region files |
