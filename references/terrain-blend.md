# Blending a build into real terrain (the part everyone gets wrong)

This file is the accumulated result of five rejected attempts. Read the failure list
first — each one is a trap you will otherwise walk into.

## The five failures, so you can recognise them

| Attempt | What it looked like | Root cause |
|---|---|---|
| 1. Box exactly arena + 45 + 45 | 26-block featureless retaining wall on all four sides | **zero columns left for a blend** — the width was fully consumed by the flat area |
| 2. Blend by noise / random stone | "random blocks.. EWW" | surface material chosen per-block from a hash |
| 3. One median height per side | grey stone masses stacked at the corners | the four sides disagree where they meet; the rim really varies along a side (y47→y73 on one edge) |
| 4. Quantised 4-block risers | a wedding cake of identical parallel rings | one lift count and one riser for the whole perimeter |
| 5. Continuous 1-block slope | contour-farmed stripes on a ramp | a ramp is not flat, and 1-block steps read as stripes |

The shape that was finally accepted: **flat lawn first, then 2-3 big steps**.

## The rule about width

```
box_width >= flat_width + 2 * blend_width
```

If `box_width == flat_width`, you have no blend and you are building a wall. Decide
this **before** generating anything.

Concrete numbers from a real project:

```
arena 100x100, requested flat extension 45 per side  ->  flat = 190 wide
box 270 wide  ->  40 columns of blend per side        ->  works
box 190 wide  ->   0 columns of blend                 ->  monolith, rejected
```

## Step 1 - measure the real rim, do not assume it is level

The ground around a build is almost never level. Measured example:

| side | natural ground | drop from plaza (y73) |
|---|---|---|
| west | y47 (bare seabed, stone/gravel) | 26 |
| south | y47 | 26 |
| north | y63-73 (grass/stone) | 0-10 |
| east | y63-71 (grass) | 2-10 |

So the blend **must** be per-side in width, depth and material. Any single-height
solution is wrong by definition.

## Step 2 - build ONE continuous rim loop

The corners are where per-side approaches die. Fix: reconcile the four profiles at
each corner, then concatenate them into a single closed loop around the box.

```python
# after sampling each side into RIM_W['W','E','N','S'] (arrays of build ly)
CB = 26
for cname, sa, ea, sb, eb in (('NW','W',0,'N',0), ('NE','E',0,'N',N-1),
                              ('SW','W',N-1,'S',0), ('SE','E',N-1,'S',N-1)):
    common = round((RIM_W[sa][ea] + RIM_W[sb][eb]) / 2)
    for side, end in ((sa, ea), (sb, eb)):
        prof = RIM_W[side]
        for k in range(CB):
            i = k if end == 0 else (N - 1 - k)
            w = 1.0 - k / float(CB)
            prof[i] = round(prof[i] * (1 - w) + common * w)

LOOP = (RIM_W['W'][0:]                       # west, north -> south
        + RIM_W['S'][1:]                     # south, west -> east
        + RIM_W['E'][N-2::-1]                # east, south -> north
        + RIM_W['N'][N-2:0:-1])              # north, east -> west
```

Because both profiles were eased to the same `common` value at the corner, `LOOP` is
continuous — and that is the only reason the terraces line up at the corners.

## Step 3 - one height field, evaluated by radial projection

For every column outside the flat area:

```python
d  = max(ox, oz)            # Chebyshev distance OUTSIDE the flat rectangle
                            # (NOT min() - min() keeps plaza height for columns that are
                            #  level with the plaza but far out on the other axis, and
                            #  then you drop off a 26-block cliff at the seam)
# project the column onto the box perimeter along a ray from the centre:
p = perimeter_param(lx, lz)          # 0 .. 4N-4, continuous
E = LOOP[p]                          # the rim height this column must reach
```

## Step 4 - flat first, then a few big steps

```python
FLAT_W = 22                      # columns of dead-flat lawn outside the plaza edge
if d <= FLAT_W:
    return LVL                   # plaza level: everything the player walks on is flat
drop = LVL - E
n = 3 if drop > 13 else 2        # NEVER more than three steps
frac = min(1.0, (d - FLAT_W) / float(TCOL - FLAT_W))
q = round(frac * n)
return LVL - round(drop * q / float(n))
```

Measured result on the accepted build: **21,940 of 36,800** outer columns dead flat,
the rest taking 2-3 steps of 8-13 blocks.

## Step 5 - riser faces

The user asked for **bare dirt under grass, no grey stone showing**:

```python
if ly == top:            put(GRASS)
elif ly >= top - 11:     put(COARSE if ((lx//7 + lz//7) & 1) else DIRT)
else:                    put(strata(ly, lx, lz))    # stone, only ever buried
```

The soil body must be **deeper than the tallest riser** or stone shows through. A
13-block riser with an 11-block dirt body is fine; with a 2-block body you get grey
bands and the "coarse_dirt stripe" look.

## Step 6 - prove it is continuous

Do not trust the render; assert on the heightmap:

```python
for dx, dz, label in ((1,0,'X'), (0,1,'Z'), (1,1,'diag')):
    bad = max(abs(TOP[z][x] - TOP[z+dz][x+dx]) for all adjacent non-plaza pairs)
    assert bad <= 3, f'{label} discontinuity {bad}'
```

The rejected corner-blend version had 228 jumps up to 26 blocks. The accepted one: **0
jumps over 3** in X, Z and diagonally. That single check is what "corners are good"
actually means.

## Step 7 - no water, ever

Two separate problems:

1. **Do not emit water.** `grep water out.nbt` -> 0 blocks. Fill every column of the box
   solid from the base to its surface so no pre-existing water is left inside.
2. **Do not expose water at the rim.** On sides where the natural ground sits under the
   sea, hold the rim at least 2 above the water surface:
   ```python
   if w is not None and 40 <= w <= 92 and abs(y - w) <= 4:
       y = max(y, w + 2)
   ```
   Otherwise the ocean shows over your terraces and the user reports "water body near
   spawn".

## Materials, if the flat part has a design

Copy the *existing* floor design rather than inventing one. In this project the main
spawn floor turned out to be a 5x4 basket-weave of `polished_granite` and `terracotta`:

```
polished_granite  if  ((x//5) + (z//4)) % 2 == 1  else  terracotta
```

Reverse-engineered by histogramming the source floor, then fitted by brute force over
`(wx, wz, offset_x, offset_z, parity)` and confirmed at **126/126 = 100%** on a clean
band. Apply it in the same coordinate space (arena-local), so the pattern continues
without a seam across the border.
