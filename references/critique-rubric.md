# Visual Critique Rubric (Mandatory Self-Review)

After `validate.py` and `quality.py` pass, render textured screenshots with `scripts/render_textured.mjs` (`hero`, `top`, `ne`, `nw`, `se`, `sw`, `eye`, `night`) plus `renders/quality-heatmap.png`, **view the actual PNG files**, and score your build `1–5` on all **8 axes** below.

> **Hard Shipping Rule:** Every axis MUST score **`>= 4`**. Any score `< 4` requires a concrete code edit, re-gate, and re-render (up to 3 refinement passes).

| # | Axis | `1–2` (Reject — Slop) | `3` (Mediocre — Refine) | `4–5` (Ship — Stunning) |
|---|---|---|---|---|
| 1 | **Instant "Wow" (`hero` & `eye`)** | Flat slab, scattered random blocks, unclear subject | Recognizable build, but sparse foreground or weak framing | Dramatic layered composition: foreground arch/trees frame water/bridge leading up to a towering hero landmark |
| 2 | **Hero Landmark** | Missing or tiny (< 8 blocks tall), plain box | Tall enough, but flat 1-plane walls or plain pyramid roof | Multi-tiered silhouette (+15–26 blocks), recessed walls, overhanging eaves, glowing accents, finial spire |
| 3 | **Zero Dead Space (`top` & heatmap)** | Empty grass/stone quadrants | Center looks busy, outer corners are bare | Every zone cell has purposeful structures, groves, camps, gardens, boulders, and curved connecting paths |
| 4 | **Custom Trees & Organics** | Vanilla-style lollipops or spheres on 1x1 sticks | Decent trunks, but solid heavy leaf balls | Flared roots on podzol, leaning tapered limbs, airy cloud-cluster canopies, swings & hanging lanterns |
| 5 | **Water & Terrain** | Pancake-flat floor, or raw square hole of water | Slight hills, plain pond edge | Rolling hills + rocky cliff outcrop, irregular pond shore with sand/mud/moss/boulders, reeds, lily pads, waterfall |
| 6 | **3D Depth & Micro-Detail** | Flush walls, unlit paths, zero furniture | Basic roofs & lamps, few props | Proud pillars, trapdoor shutters, tents with gear, cooking spit, benches, market stalls, petal/flora clusters |
| 7 | **Colour & Night Atmosphere (`night`)** | Clashing random palette, pitch-black at night | Cohesive blocks, uneven dark patches | Harmonious theme palette; warm lanterns, campfires & submerged pond lights glow invitingly in the `night` render |
| 8 | **Player Sightline & Walkability (`eye-spawn`)** | Spawn faces a wall, tree trunk, or empty rim | Spawn faces center, path requires awkward 2-block jumps | Spawn faces straight down an inviting lantern-lit path/gate toward the hero view; bridges & steps use smooth slabs/stairs |
