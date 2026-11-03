# Build assets (`assets/`)

`assets/` holds per-build `.nbt` files extracted from **your local copy** of
`all-builds.zip` — a bundle of third-party packs (ArtillexStudios, KubecStudios,
Exo Elight, BoutiqueBuilds, Valtury, …) — plus a `catalog.json` index of them.

**They are intentionally NOT committed to this repository.** They are other
studios' builds; redistributing them in a public repo would breach their
licences. The extracted files are also large (thousands of individual builds).

## Regenerating locally

You need the original archive. Then:

```bash
python3 scripts/extract_all_builds.py ~/Downloads/all-builds.zip
```

This unzips the packs (`.zip`, `.rar` via `7z`), walks every Sponge `.schem`,
`.schematic`, `.litematic` and world export, splits the grid sheets into
individual builds with `scripts/mckit/schem.py`, and writes `assets/<category>/`
plus `assets/catalog.json`.

## Using them as reference

The example builds read from `assets/` at build time. Treat the assets the way
this skill's `references/design-principles.md` says: **study them for scale,
silhouette and palette — never paste a schematic you did not generate.** The
pipeline in `mckit` generates every block procedurally; the assets only inform
proportions and block pairings.

> Attribution for the upstream skill material lives in `CREDITS.md`. Attribution
> for the third-party build packs belongs to their respective authors and is
> recorded in `assets/catalog.json` when you regenerate it.
