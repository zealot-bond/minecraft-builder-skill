#!/usr/bin/env python3
"""Example 02 - the blend that survived review: flat lawn, then 2-3 big steps,
with ONE continuous rim loop so the corners line up.

The ground here is synthetic (a tilted plane) so the example runs with no world
files; in a real project you replace `ground_at()` with
`read_region.py --box ... --csv ground.csv`.

Run:  python3 build.py    (prints the continuity proof)
"""
import math

N = 120
P0, P1 = 20, 99          # the flat plaza (80 wide) inside a 120 box -> 20 of blend/side
TCOL = P0
LVL = 31
FLAT_W = 8
Y0 = 42


def ground_at(lx, lz):
    """Stand-in for measured terrain: high in the east, low in the west."""
    return int(round(63 + (lx / float(N - 1)) * 10 - (lz / float(N - 1)) * 4))


def slope_limit(v, maxd, passes=60):
    v = list(v)
    for _ in range(passes):
        moved = False
        for i in range(len(v) - 1):
            if v[i + 1] > v[i] + maxd: v[i + 1] = v[i] + maxd; moved = True
            elif v[i + 1] < v[i] - maxd: v[i + 1] = v[i] - maxd; moved = True
        for i in range(len(v) - 2, -1, -1):
            if v[i] > v[i + 1] + maxd: v[i] = v[i + 1] + maxd; moved = True
            elif v[i] < v[i + 1] - maxd: v[i] = v[i + 1] - maxd; moved = True
        if not moved: break
    return v


# --- rim profiles, one per side, then reconciled at the corners -------------
RIM = {
    'W': slope_limit([max(4, ground_at(0, z) - Y0) for z in range(N)], 1),
    'E': slope_limit([max(4, ground_at(N - 1, z) - Y0) for z in range(N)], 1),
    'N': slope_limit([max(4, ground_at(x, 0) - Y0) for x in range(N)], 1),
    'S': slope_limit([max(4, ground_at(x, N - 1) - Y0) for x in range(N)], 1),
}
CB = 12
CORNER = {}
for name, sa, ea, sb, eb in (('NW','W',0,'N',0), ('NE','E',0,'N',N-1),
                             ('SW','W',N-1,'S',0), ('SE','E',N-1,'S',N-1)):
    common = int(round((RIM[sa][ea] + RIM[sb][eb]) / 2.0))
    CORNER[name] = common
    for side, end in ((sa, ea), (sb, eb)):
        p = RIM[side]
        for k in range(CB):
            i = k if end == 0 else (N - 1 - k)
            w = 1.0 - k / float(CB)
            p[i] = int(round(p[i] * (1 - w) + common * w))

LOOP = (RIM['W'][:] + RIM['S'][1:] + RIM['E'][N - 2::-1] + RIM['N'][N - 2:0:-1])
LN = len(LOOP)

def loop_at(p):
    return LOOP[int(p) % LN]


def top_of(lx, lz):
    ox = P0 - lx if lx < P0 else (lx - P1 if lx > P1 else 0)
    oz = P0 - lz if lz < P0 else (lz - P1 if lz > P1 else 0)
    if ox == 0 and oz == 0:
        return LVL
    d = max(ox, oz)
    if d <= FLAT_W:
        return LVL                                  # dead flat, like the plaza
    cx = cz = (N - 1) / 2.0
    dx, dz = lx - cx, lz - cz
    t = min((N - 1) / 2.0 / abs(dx) if dx else 1e9,
            (N - 1) / 2.0 / abs(dz) if dz else 1e9)
    hx, hz = cx + dx * t, cz + dz * t
    if hx <= 0.5:            p = hz
    elif hz >= N - 1.5:      p = (N - 1) + hx
    elif hx >= N - 1.5:      p = 2 * (N - 1) + (N - 1 - hz)
    else:                    p = 3 * (N - 1) + (N - 1 - hx)
    E = float(loop_at(round(p)))
    drop = LVL - E
    if drop <= 0:
        return LVL
    n = 3 if drop > 13 else 2                       # never more than three steps
    frac = min(1.0, (d - FLAT_W) / float(TCOL - FLAT_W))
    return LVL - int(round(drop * round(frac * n) / float(n)))


TOP = [[top_of(x, z) for x in range(N)] for z in range(N)]

# Final guarantee: relax the finished heightmap so no two adjacent columns differ by
# more than MAXD. Doing this on the RIM alone is not enough - the radial projection
# can jump several rim samples across a corner, and that is what produced the ragged
# diagonal steps in the rejected version.
MAXD = 3


def relax(grid, maxd, passes=40):
    n = len(grid)
    for _ in range(passes):
        moved = False
        for z in range(n):
            row = grid[z]
            for x in range(n - 1):
                if row[x + 1] > row[x] + maxd: row[x + 1] = row[x] + maxd; moved = True
                elif row[x + 1] < row[x] - maxd: row[x + 1] = row[x] - maxd; moved = True
            for x in range(n - 2, -1, -1):
                if row[x] > row[x + 1] + maxd: row[x] = row[x + 1] + maxd; moved = True
                elif row[x] < row[x + 1] - maxd: row[x] = row[x + 1] - maxd; moved = True
        for x in range(n):
            for z in range(n - 1):
                if grid[z + 1][x] > grid[z][x] + maxd: grid[z + 1][x] = grid[z][x] + maxd; moved = True
                elif grid[z + 1][x] < grid[z][x] - maxd: grid[z + 1][x] = grid[z][x] - maxd; moved = True
            for z in range(n - 2, -1, -1):
                if grid[z][x] > grid[z + 1][x] + maxd: grid[z][x] = grid[z + 1][x] + maxd; moved = True
                elif grid[z][x] < grid[z + 1][x] - maxd: grid[z][x] = grid[z + 1][x] - maxd; moved = True
        if not moved:
            break
    return grid


relax(TOP, MAXD)
flat = sum(1 for z in range(N) for x in range(N) if TOP[z][x] == LVL)
print('columns %d, flat at plaza level %d (%.0f%%)'
      % (N * N, flat, 100.0 * flat / (N * N)))
worst = 0
for z in range(N):
    for x in range(N - 1):
        worst = max(worst, abs(TOP[z][x] - TOP[z][x + 1]))
for z in range(N - 1):
    for x in range(N):
        worst = max(worst, abs(TOP[z][x] - TOP[z + 1][x]))
diag = max(abs(TOP[z][x] - TOP[z + 1][x + 1])
           for z in range(N - 1) for x in range(N - 1))
print('continuity: max adjacent jump X/Z = %d, diagonal = %d (limit %d)'
      % (worst, diag, MAXD))
print('corner heights:', CORNER)
# A diagonal may legitimately differ by up to 2*MAXD even when every orthogonal
# neighbour is within MAXD - do not confuse the two limits.
assert worst <= MAXD, 'blend is discontinuous (orthogonal)'
assert diag <= 2 * MAXD, 'blend is discontinuous (diagonal)'
print('OK - feed TOP into your block generator (see examples/04-full-spawn)')
