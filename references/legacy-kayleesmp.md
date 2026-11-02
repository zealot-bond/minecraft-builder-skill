# Legacy Live-World Constraints (`kayleesmp` / `project.json`)

The original v1 rules of this skill were distilled from fixing a live server build (`macetopia`, shown in `examples/04-full-spawn/`) that pasted into existing ocean/land `.mca` region files under strict server plugin constraints.

Those constraints **do NOT apply by default** to standalone spawns, hubs, or schematics. Turn them on via `project.json` only when a live server specifically requires them:

```json
{
  "data_version": 5023,
  "no_water": true,
  "flat_floor": 31,
  "whitelist": [
    "oak_wood", "jungle_wood", "oak_leaves", "jungle_leaves",
    "grass_block", "dirt", "coarse_dirt", "stone"
  ],
  "quality": {
    "min_relief_std": 0.0
  }
}
```

## When Blending Into Existing `.mca` World Terrain
If the user supplies a `world/region/` directory and wants a build blended seamlessly into existing surrounding chunks rather than a standalone island plot:
1. Measure ground heights and `DataVersion` first with `scripts/read_region.py` (`references/region-read.md`).
2. Ensure `box_width >= flat_width + 2 * blend_width` and construct one continuous perimeter rim loop (`references/terrain-blend.md`).
3. Validate surface continuity with `python3 scripts/validate.py out.nbt --blend 0 0 269 269 --max-jump 3` and prove the live FAWE paste with the void identity (`references/fawe-paste.md`).
