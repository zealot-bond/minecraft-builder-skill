# Verification: the checks that stop "it looked fine to me"

Every rule below exists because a human rejected the build for exactly that defect.
Run them all. `scripts/validate.py` implements them and exits non-zero on failure.

## The pass/fail list

| # | Check | Pass condition | The complaint it prevents |
|---|---|---|---|
| 1 | Bounds | every `pos` inside `size` | "everything was misaligned" |
| 2 | Palette | index 0 is `air`; no duplicate states | corrupt file |
| 3 | Round trip | file re-parses; block count == declared | `struct.error`, truncated NBT |
| 4 | Flatness | every walkable column has a block at its surface level | "holes", "you can fall through" |
| 5 | Continuity | no adjacent surface height jump > 3 | "corners are overlapping, not perfect" |
| 6 | Floating foliage | 0 leaf/wood components below the floor level | "floating trees", "floating grass" |
| 7 | Plant support | every plant/wall block has a valid support | "floating grass", "heads in the air" |
| 8 | Soil on trees | 0 grass/moss/dirt blocks resting on a log or leaf | "random grass blocks on the trees" |
| 9 | Water | 0 water blocks unless deliberately designed | "no water body near spawn" |
| 10 | Tripwire | 0, unless deliberately designed | "random floating strings" |
| 11 | Banners/signs | backing block behind the stated facing is solid | "banners not at right positions" |
| 12 | Openings | designed openings (ladder shafts, doorways) still open | "the ladder is capped" |
| 13 | Void | `//count minecraft:structure_void` == 0 after paste | invisible junk |
| 14 | Box arithmetic | `void_replaced == sx*sy*sz - blocks` | incomplete paste |

## The three that catch almost everything

**Floating components.** Connected-component sweep over the structural block family,
seeded from the floor; anything not reachable and smaller than a threshold is deleted.
This is how 1,788 leaf blocks floating 3-8 blocks above a floor were found:

```python
# returns (kept, removed) - anything not connected to a surface block
comps = connected_components(blocks, family=LEAVES_AND_WOOD, connectivity=6)
floating = [c for c in comps if min(p[1] for p in c) > FLOOR_LY + 1]
```

Report it as a number: *"78 tree components, 78 grounded, 0 floating"*. A build is not
done until that line reads 0.

**Support for decorative blocks.** Look *below*, not at all six neighbours:

```python
if idx in FLAT_PLANTS:                     # short_grass, moss_carpet, flowers...
    if below is AIR or below in NOSUPPORT:
        remove()
```
`NOSUPPORT` must include leaves, logs, `iron_chain`, `lantern`, `scaffolding`, panes —
otherwise a plant left on a leaf survives and reads as "grass growing on the tree".

**Soil resting on a tree.** Check the block *below* only:

```python
if idx in SOILS and below_block in (WOODS | LEAVES):
    remove()
```
Do **not** check all six neighbours: a grass block under a canopy is correct, and a
6-neighbour rule punches holes in the ground beneath every tree (measured: it deleted
the surface under 240 columns).

## Traps in writing these checks

- **`array('H')` and signed values.** A per-column top array wants `array('b')` if you
  store `-1` for "inside the plaza" — `'H'` cannot hold negatives.
- **`PAL` entries are tuples**, not dicts: `(name, tuple(sorted(props.items())))`. Read
  properties with `dict(pr).get('facing')`, or you get
  `AttributeError: 'tuple' object has no attribute 'get'`.
- **`pkill -f <pattern>` matches your own shell** if the pattern appears in the command
  line, killing the command mid-run. Use a bracketed pattern (`chrome-linux64/[c]hrome`).
- **Long background jobs die with the shell.** Start them detached
  (`setsid nohup ... & disown`) and never `sleep` inside the same call for the full
  duration — the tool timeout kills the process group.

## Rendering before pasting is not optional

A model that has not looked at a render is guessing. Both a machine check and a visual
check, every time:

```bash
python3 scripts/render3d.py out.nbt --views iso,top,low,corner --outdir renders/
python3 scripts/chunk_sheet.py out.nbt --box 85 85 100 100 --tiles 4 --out renders/arena-sheet.png
```

The per-chunk contact sheet is what turns "the arena feels like slop" into concrete
findings: floating canopies, misplaced banners and bare patches all show up immediately
in a 4x4 grid of 25-block tiles, and are invisible in one wide shot.

## What "verified" is allowed to mean

Only these two count:

1. **Exact block-count agreement** between the source NBT and the live world
   (`//count <block>` == source count, for several distinctive blocks).
2. **The box arithmetic identity** `void_replaced == sx*sy*sz - blocks`.

Do not report success from: a console line saying the paste happened, a region file that
looks different, or a render you made from your own NBT instead of the world.
