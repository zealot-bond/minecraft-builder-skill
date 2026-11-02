# minecraft-builder-skill (v2 — Design-First + Verified)

An AI agent skill & procedural toolkit (`mckit`) that turns prompts like *"create a 50x50 cool spawn"* into **richly composed, themed, watertight, zero-dead-space Minecraft Java schematics** — backed by real-texture WebGL rendering and two strict gates that block both broken blocks *and* lazy flat slabs.

```bash
# 1. Generate a gold-standard 50x50 spawn with mckit
python3 examples/05-sakura-pond-camp/build.py

# 2. GATE 1 (Structural): 0 floating leaves, 0 water leaks, persistent leaves, valid supports
python3 scripts/validate.py examples/05-sakura-pond-camp/sakura-pond-camp.nbt --strict

# 3. GATE 2 (Anti-Empty Quality): 0 dead zone cells, terrain relief, hero landmark, lighting, coherence
python3 scripts/quality.py examples/05-sakura-pond-camp/sakura-pond-camp.nbt

# 4. Render 8 real-texture views (hero, top, 4 corners, player eye-level, night) via Lodestone + Three.js
node scripts/render_textured.mjs examples/05-sakura-pond-camp/sakura-pond-camp.nbt \
        --outdir examples/05-sakura-pond-camp/renders

# 5. Run unit tests (verifies toolkit, watertight ponds, grounded trees, and that flat slabs FAIL quality.py)
npm test
```

## Why v2 Exists

v1 of this skill only encoded *defect avoidance* from a single flat-arena project — so when asked for a *"50x50 cool spawn"*, agents played it safe and emitted a flat, mostly-empty square that scored a perfect `PASS`.

v2 keeps every byte-level NBT and structural correctness invariant and adds the missing half:
1. **Art-Director Pipeline (`SKILL.md`, `templates/design.md`):** Auto-picks a vivid theme (`sakura`, `samurai`, `golden_autumn`, `futuristic`, `vanilla_plus`, `fantasy`), runs web searches for inspiration, brainstorms 12+ features, and maps every cell of the plot in a `ZoneGrid` before placing a single block.
2. **High-Level Procedural Toolkit (`scripts/mckit/`):**
   - `Canvas` with named `with c.part(...):` hierarchy, automatic fence/wall/pane connections, and `.manifest.json` export.
   - `terrain`: sculpted standalone islands with craggy undersides, 100% watertight koi ponds with lily pads & submerged glow, rock-cradled waterfalls, curved Bézier paths, mossy boulders, and meadow flora.
   - `trees`: 9 organic tree species (`sakura`, `giant_oak`, `weeping_willow`, `japanese_pine`, `autumn_maple`, `birch_grove`, `spruce`, `azalea`, `neon_tree`) + `bamboo_clump` with flared roots, 6-connected tapered limbs, "cluster & subtract" canopies, and horizontal swing branches.
   - `props`: 3-tier Pagoda Shrines, Holo Energy Spires, arched Drum Bridges, Torii Gates, Campfire Camps (with cooking spits, log benches & striped A-frame tents), Tea Pavilions, Fishing Piers, Market Stalls, Zen Rock Gardens, Tree Swings, Tōrō Lanterns, Benches & Compass Spawn Pads.
3. **Anti-Emptiness Gate (`scripts/quality.py`):** Rejects flat slabs, single-block monocultures, missing landmarks, unlit builds, and empty zone cells (emitting `renders/quality-heatmap.png` so the agent sees exactly which chunk needs work).
4. **Headless Real-Texture Renderer (`scripts/render_textured.mjs`):** Renders daytime, golden-hour, night-time, bird's-eye, 4-corner, and player-eye views with real Minecraft block models & textures via `@mattzh72/lodestone` + Three.js, paired with an 8-axis visual critique rubric (`references/critique-rubric.md`).

## Requirements

- **Python 3.9+** (stdlib only; `Pillow` for `quality-heatmap.png` / fallback `render3d.py`)
- **Node 21+** (`npm install` installs `@mattzh72/lodestone`, `three`, `gl-matrix`, `vite`) + Chromium (`chrome-headless-shell` / `chromium` auto-detected) for `scripts/render_textured.mjs`

## Credits & Licence

MIT (`LICENSE`). Builds on [`wzhaoMS/minecraft-builder-skill`](https://github.com/wzhaoMS/minecraft-builder-skill) and [`mattzh72/minecraft-builder-skill`](https://github.com/mattzh72/minecraft-builder-skill) (`@mattzh72/lodestone`); see `CREDITS.md` and `vendor/`.
