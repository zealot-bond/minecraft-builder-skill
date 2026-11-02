# minecraft-builder-skill

Build Minecraft Java structures that **actually land where you meant them to**, with a
verification gate that refuses to let you paste a broken build.

Distilled from a real spawn rebuild that was rejected five times. Every rule here is a
defect that was measured, diagnosed and fixed — not a style opinion.

```bash
# 1. measure the real world (never guess terrain)
python3 scripts/read_region.py --dir world/region --box 195 259 270 270 --side-medians

# 2. generate  (see examples/)
python3 examples/01-flat-plaza/build.py

# 3. GATE: refuses to pass on floating blocks, holes, water, misplaced decoration
python3 scripts/validate.py mybuild.nbt --floor 31 --flat 40 40 229 229 --strict

# 4. look at it  (few blocks are obvious in a wide shot; tiles are not)
python3 scripts/render3d.py mybuild.nbt --views iso,top --outdir renders/
python3 scripts/chunk_sheet.py mybuild.nbt --box 85 85 100 100 --tiles 4 --out sheet.png

# 5. render the pretty one on Shulkr and screenshot it
node scripts/shulkr_shot.mjs --nbt mybuild.nbt --out renders/shulkr.png

# 6. ship the pastable schematic + FAWE commands with the arithmetic checked
python3 scripts/paste_commands.py --pos 195 42 259 --size 270 98 270 \
        --schem mybuild --blocks 2126796 --count minecraft:polished_granite
```

## What makes it different

**It refuses to report success on vibes.** A paste counts only when
`//count <block>` equals your source count *and* the void replacement equals
`sx*sy*sz - blocks`. That identity is a complete-paste proof for free.

**It encodes the failure modes, with the numbers that diagnosed them:**

| Symptom the user reported | Actual cause | Measured |
|---|---|---|
| "ugly 26-block retaining wall" | box width == flat width, zero blend columns | `N=190 = 100 + 45 + 45` |
| "corners are overlapping" | per-side heights disagree at corners | 228 jumps up to 26 blocks |
| "main terrain is weird" | quantised 4-block risers everywhere | 25 lifts, wedding cake |
| "random floating strings" | `tripwire` needs no support | 22 blocks, all air underneath |
| "banners not at right positions" | no wall behind the stated facing | 79 of 80 unsupported |
| "random grass on the trees" | soil resting on logs/leaves | 286 blocks |
| "floating trees" | canopies with no trunk | 68 of 81, 1,788 blocks |
| "grey stone on the dirt risers" | soil body shallower than the riser | 2 vs 13 |

**It contains the low-level traps** that silently corrupt files: the compound-inside-a-TAG_List
byte layout that makes an NBT unparseable, `array('H')` vs `array('b')`, region sections
that must be read ascending or every height is wrong, `pkill -f` killing its own shell,
and background jobs dying with the tool call that started them.

## Install

Python 3.9+ (stdlib only) for everything except:

- `scripts/shulkr_shot.mjs` — Node 21+ and a Chromium binary (for the Shulkr screenshot).
- `vendor/lodestone-*` — the upstream Lodestone recipe/render path (`npm install` there).

No `pip install` is required. `render3d.py` needs Pillow.

## Layout

```
SKILL.md                  the agent-facing contract and pipeline
references/               blockstates, NBT layout, FAWE semantics, region reading,
                          terrain blending, verification, pitfalls
scripts/                  streamnbt, validate, nbt_query, render3d, chunk_sheet,
                          read_region, paste_commands, trees, shulkr_shot
examples/                 01 flat plaza, 02 terrain blend, 03 parquet ring, 04 full spawn
vendor/                   upstream Lodestone docs/scripts/assets + mcb blueprints
```

## Built on

- [`wzhaoMS/minecraft-builder-skill`](https://github.com/wzhaoMS/minecraft-builder-skill)
  — the `mcb` CLI: preview PNGs an agent can read, verify-after-build, undo, blueprints.
- [`mattzh72/minecraft-builder-skill`](https://github.com/mattzh72/minecraft-builder-skill)
  — Lodestone-backed recipes, structure-NBT output, the block-state reference docs.

Both are MIT; see `CREDITS.md` and `vendor/`.

## Licence

MIT. See `LICENSE`.
