# Example 05 — Harbor & Highland Trading Post (`317x176x249`)

Expansive multi-building trading settlement from `all-builds.zip` demonstrating multi-house village clustering, docks, cranes, and terrain terracing.

## Build Specifications
- **Dimensions:** `317 x 176 x 249` (`Width x Height x Length`)
- **Non-Air Blocks:** `707,737`
- **Unique Blockstates:** `587`
- **Files:** `trading-post.schem` (WorldEdit/FAWE) · `trading-post.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
| `cobbled_deepslate` | 174,230 | 24.6% |
| `mud` | 151,021 | 21.3% |
| `dirt` | 147,482 | 20.8% |
| `mossy_cobblestone` | 101,052 | 14.3% |
| `tuff` | 30,724 | 4.3% |
| `moss_block` | 16,246 | 2.3% |
| `short_grass` | 13,346 | 1.9% |
| `spruce_leaves` | 10,427 | 1.5% |
| `cyan_terracotta` | 8,663 | 1.2% |
| `grass_block` | 7,676 | 1.1% |
| `birch_leaves` | 4,571 | 0.6% |
| `rooted_dirt` | 4,175 | 0.6% |

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py trading-post.nbt --summary --top 25
node ../../scripts/render_textured.mjs trading-post.nbt --shots hero,top,night --outdir renders/
```
