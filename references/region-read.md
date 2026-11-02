# Reading a live world from `.mca` region files

You need this to answer the only question that matters when blending a build into a
world: **what is the real ground height here?** Guessing it is how you get a 26-block
retaining wall the user calls ugly.

## File layout

A region file `r.<rx>.<rz>.mca` holds chunks `(cx, cz)` where `cx>>5 == rx`.

```
offset = u32 at byte 4*((cx & 31) + (cz & 31)*32)
if offset == 0: chunk not generated
block_off = (offset >> 8) * 4096
length    = u32 at block_off            (includes the 4-byte length itself)
comp      = byte at block_off + 4       1 = gzip, 2 = zlib, 3 = uncompressed
body      = bytes[block_off+5 : block_off+4+length]
```

Region `r.0.0` covers `x 0..511, z 0..511`. **A build box that reaches `z >= 512`
needs `r.0.1` too** — reading only `r.0.0` silently returns "no chunk" for half the
box and you will think the terrain is missing.

## Chunk sections

```
Level
└── sections[]              one per 16-block vertical slab
    ├── Y                   section index: block y = Y*16 + local_y
    └── block_states
        ├── palette[]       list of {Name, Properties?}
        └── data[]          packed longs, only when palette length > 1
```

Palette index of local block `(lx, ly, lz)` inside a section:

```python
bits = max(4, (len(palette) - 1).bit_length())
per  = 64 // bits                     # indices per long
i    = ly * 256 + lz * 16 + lx
v    = (data[i // per] >> ((i % per) * bits)) & ((1 << bits) - 1)
name = palette[v]
```

`bits` has a **minimum of 4** even for tiny palettes. If `data` is absent there is
exactly one block in the section — index 0 everywhere.

## THE BUG that makes the terrain look wrong: section order

Sections in the NBT list are **not** guaranteed sorted. And "find the surface" wants
the *topmost* solid block.

```python
# WRONG - first write wins, and the list order may be arbitrary,
# so you record the LOWEST solid block. Symptom: median surface y=-49,
# zero water found, and the "usable column" count collapses.
for sec in sections:
    ...
    if solid: out = y; break

# RIGHT - ascending sections, last write wins == highest solid
for sec in sorted(sections, key=lambda s: s['Y']):
    for ly in range(15, -1, -1):
        ...
        if solid: out = base + ly; break
```

Getting this backwards produced `usable 861` instead of `58209`, and per-side medians of
`-49`. Everything downstream (terrace heights, water masking) was garbage.

## Skip decorative blocks, not structural ones

A surface scan must ignore vegetation or you will think the ground is 8 blocks higher
than it is. Skip (but do **not** skip stone/dirt/gravel/sand):

```
air cave_air void_air short_grass tall_grass fern large_fern poppy dandelion
red_tulip lily_of_the_valley pink_petals leaf_litter firefly_bush
*_leaves *_log *_wood bamboo sugar_cane snow moss_carpet moss_block
player_head skeleton_skull candle sea_pickle ... (see vendor list in
scripts/read_region.py)
```

## Water is not ground, and underground water is not the sea

Record water separately:

```python
if name in ('water', 'lava'):
    wat = base + ly      # continue: keep the highest
    continue
```

Then when you mask terrain against water, **only surface water may lift the ground**:

```python
if w is not None and abs(y - w) <= 4:      # a real lake / sea next to the ground
    y = max(y, w + 2)
# an underground pond 40 blocks below must NOT raise anything
```

Without that guard, a cave pond at `y=6` lifts the terrain above it and you build a
plateau in the wrong place.

## Reject cave artefacts

The topmost "solid" block in a column that happens to sit over a cavern is the
**cavern floor** — a real measurement produced `y = -17` among a seabed of `y = 47`.
Filter to plausible ground before taking any median:

```python
if not (40 <= y <= 92): return None       # not ground
```

Then gap-fill from the nearest valid sample and **median-filter along the feature**
(+/- a dozen columns), never per column. Per-column noise is what reads to a player as
"random blocks".

## Usage

```bash
python3 scripts/read_region.py --dir world/region --box 195 259 270 270 --csv ground.csv
python3 scripts/read_region.py --at 300 394            # one column: surface + water
python3 scripts/read_region.py --dataversion           # DataVersion for your NBT
```
