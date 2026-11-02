# Examples

| # | What it teaches | Runs standalone? |
|---|---|---|
| 01-flat-plaza | palette grid, air at index 0, one flat surface, NBT write | yes |
| 02-terrain-blend | continuous rim loop, flat lawn + 2-3 big steps, continuity proof | yes (synthetic ground) |
| 03-parquet-ring | fit an existing floor rule, then continue it past the border | yes |
| 04-full-spawn | the complete 270x270 generator this skill came from | no — needs the project's arena NBT and region files |

Every example writes an `.nbt` you can then run through the scripts:

```bash
python3 examples/01-flat-plaza/build.py
python3 scripts/validate.py examples/01-flat-plaza/flat-plaza.nbt \
        --floor 8 --flat 2 2 45 45
python3 scripts/render3d.py examples/01-flat-plaza/flat-plaza.nbt \
        --views iso,top --outdir /tmp/r
```

`04-full-spawn/build.py` is the real generator, kept verbatim because it contains the
whole working pipeline: arena restore, de-slop sweep, tree replant, cave, terrain field,
parquet ring, clean-ups and the streaming write. Read it as the reference implementation
rather than running it.
