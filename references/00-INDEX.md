# Reference Index

Read in this order when creating a new spawn, hub, or schematic.

## 1. Before You Write Code (Design & Planning)
1. **`templates/design.md`** — Copy into your build folder and fill out theme, inspiration digest, palette, hero sightline, and ASCII zone map **before** placing blocks.
2. **`references/themes/`** (`sakura.md`, `samurai.md`, `golden-autumn.md`, `futuristic.md`, `vanilla-plus.md`, `fantasy.md`) — Ready-to-use palettes, gradients, signature landmarks, and search queries.
3. **`references/inspiration.md`** — How to run web searches for showcase builds & custom tree silhouettes and turn them into concrete design cues.
4. **`references/feature-catalog.md`** — Brainstorm menu of 20+ landmarks, water features, bridges, camps, groves, and props with `mckit` helpers.
5. **`references/design-principles.md`** — Three scales of detail, the 3-block wall depth rule, vertical/horizontal gradients, custom tree anatomy, and sightline framing.

## 2. While Generating (`scripts/mckit`, `assets/` & NBT)
6. **`examples/06-grand-haven-150x150/build.py`** & **`examples/01..05/`** — Flagship `150x150` hybrid generator (`mckit` + stamped `assets/`) and 5 full-scale curated reference spawns.
7. **`references/blockstates.md`** — Block state properties and support rules (handled automatically by `mckit.Canvas`, documented for custom blocks).
8. **`references/structure-nbt.md`** — Streaming vanilla `.nbt` format layout.

## 3. Gates, Textured Rendering & Visual Critique
9. **`references/verification.md`** — Structural (`validate.py`) and anti-emptiness (`quality.py`) pass conditions.
10. **`references/critique-rubric.md`** — 8-axis visual rubric (`>= 4/5` required on every axis after inspecting `render_textured.mjs` PNGs).

## 4. Delivering or Blending Into Live Worlds
11. **`references/fawe-paste.md`** — FAWE paste anchoring and the void-replacement completeness proof.
12. **`references/legacy-kayleesmp.md`**, **`references/terrain-blend.md`**, **`references/region-read.md`** — Optional `project.json` constraints and `.mca` terrain blending when pasting into existing survival terrain.
13. **`references/shulkr-viewer.md`**, **`references/pitfalls.md`** — Browser/WebGL/shell troubleshooting.
