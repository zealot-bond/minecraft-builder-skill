# Example 03 — Survival Woodland Spawn (`133x106x151`)

Full-scale survival spawn build from `all-builds.zip` blending organic cliffs, custom conifers/oaks, pathways, and rustic timber architecture.

## Build Specifications
- **Dimensions:** `133 x 106 x 151` (`Width x Height x Length`)
- **Non-Air Blocks:** `55,090`
- **Unique Blockstates:** `230`
- **Files:** `survival-spawn.schem` (WorldEdit/FAWE) · `survival-spawn.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
| `grass_block` | 14,167 | 25.7% |
| `red_wool` | 10,396 | 18.9% |
| `coarse_dirt` | 5,683 | 10.3% |
| `brown_mushroom_block` | 5,078 | 9.2% |
| `brown_wool` | 3,848 | 7.0% |
| `oak_leaves` | 3,676 | 6.7% |
| `grass` | 1,465 | 2.7% |
| `oak_wood` | 1,289 | 2.3% |
| `stone` | 717 | 1.3% |
| `dirt_path` | 686 | 1.2% |
| `jungle_leaves` | 490 | 0.9% |
| `spruce_stairs` | 481 | 0.9% |

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py survival-spawn.nbt --summary --top 25
node ../../scripts/render_textured.mjs survival-spawn.nbt --shots hero,top,night --outdir renders/
```
