# Example 02 — Japanese Spring Sanctuary (`100x58x100`)

100x100 Japanese spring sanctuary from `all-builds.zip` showcasing traditional curved roofs, blossom trees, lantern paths, and sculpted terrain.

## Build Specifications
- **Dimensions:** `100 x 58 x 100` (`Width x Height x Length`)
- **Non-Air Blocks:** `52,515`
- **Unique Blockstates:** `502`
- **Files:** `japanese-spring-spawn.schem` (WorldEdit/FAWE) · `japanese-spring-spawn.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
| `dirt` | 15,092 | 28.7% |
| `grass_block` | 7,319 | 13.9% |
| `bamboo` | 3,107 | 5.9% |
| `grass` | 1,910 | 3.6% |
| `magenta_terracotta` | 1,837 | 3.5% |
| `pink_wool` | 1,835 | 3.5% |
| `pink_stained_glass_pane` | 1,759 | 3.3% |
| `magenta_stained_glass` | 1,753 | 3.3% |
| `spruce_planks` | 1,364 | 2.6% |
| `oak_wood` | 1,190 | 2.3% |
| `stripped_dark_oak_log` | 944 | 1.8% |
| `stone` | 849 | 1.6% |

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py japanese-spring-spawn.nbt --summary --top 25
node ../../scripts/render_textured.mjs japanese-spring-spawn.nbt --shots hero,top,night --outdir renders/
```
