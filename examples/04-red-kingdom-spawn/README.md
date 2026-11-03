# Example 04 — Red Kingdom Citadel Spawn (`190x179x190`)

Grand 190x190 crimson-and-stone castle kingdom spawn from `all-builds.zip` (DataVersion 5023 / 26.3) demonstrating monumental fortress massing and courtyard hierarchy.

## Build Specifications
- **Dimensions:** `190 x 179 x 190` (`Width x Height x Length`)
- **Non-Air Blocks:** `384,198`
- **Unique Blockstates:** `837`
- **Files:** `red-kingdom-spawn.schem` (WorldEdit/FAWE) · `red-kingdom-spawn.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
| `brown_concrete_powder` | 90,691 | 23.6% |
| `light_gray_terracotta` | 74,466 | 19.4% |
| `brown_wool` | 73,525 | 19.1% |
| `brown_concrete` | 50,700 | 13.2% |
| `packed_mud` | 26,256 | 6.8% |
| `brown_mushroom_block` | 18,797 | 4.9% |
| `moss_block` | 6,723 | 1.7% |
| `grass_block` | 5,091 | 1.3% |
| `azalea_leaves` | 3,479 | 0.9% |
| `birch_leaves` | 3,186 | 0.8% |
| `short_grass` | 2,745 | 0.7% |
| `oak_leaves` | 2,453 | 0.6% |

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py red-kingdom-spawn.nbt --summary --top 25
node ../../scripts/render_textured.mjs red-kingdom-spawn.nbt --shots hero,top,night --outdir renders/
```
