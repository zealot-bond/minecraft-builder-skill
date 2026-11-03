# Example 01 — Economy SMP Spawn (`78x81x78`)

Compact medieval/fantasy Economy SMP hub from `all-builds.zip` featuring an elevated central plaza, steep timber-and-stone towers, custom trees, and market stalls.

## Build Specifications
- **Dimensions:** `78 x 81 x 78` (`Width x Height x Length`)
- **Non-Air Blocks:** `111,528`
- **Unique Blockstates:** `429`
- **Files:** `economy-smp-spawn.schem` (WorldEdit/FAWE) · `economy-smp-spawn.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
| `grass_block` | 88,519 | 79.4% |
| `red_concrete` | 7,178 | 6.4% |
| `azalea_leaves` | 3,102 | 2.8% |
| `short_grass` | 1,461 | 1.3% |
| `dirt` | 1,161 | 1.0% |
| `mangrove_leaves` | 965 | 0.9% |
| `tall_grass` | 732 | 0.7% |
| `spruce_trapdoor` | 596 | 0.5% |
| `brown_mushroom_block` | 447 | 0.4% |
| `rooted_dirt` | 405 | 0.4% |
| `white_wool` | 329 | 0.3% |
| `spruce_stairs` | 328 | 0.3% |

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py economy-smp-spawn.nbt --summary --top 25
node ../../scripts/render_textured.mjs economy-smp-spawn.nbt --shots hero,top,night --outdir renders/
```
