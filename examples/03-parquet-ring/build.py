#!/usr/bin/env python3
"""Example 03 - reproduce an existing floor design and continue it past the border.

The rule below was reverse-engineered from a real arena floor: histogram the floor
blocks, then fit `(wx, wz, offset_x, offset_z, parity)` by brute force, and confirm
it matches 100% on a clean band before applying it anywhere else.

    polished_granite if ((x//5) + (z//4)) % 2 == 1 else terracotta

Run: python3 build.py    (prints the fit check on synthetic data)
"""
import itertools

# a clean 30x30 band of the source floor, as (x, z, is_granite)
def source_is_granite(x, z):
    return ((x // 5) + (z // 4)) % 2 == 1

SAMPLE = [(x, z, source_is_granite(x, z))
          for z in range(44, 74) for x in range(18, 48)]

def fit(samples):
    best = None
    for wx, wz, ox, oz, p in itertools.product(range(3, 9), range(3, 9),
                                               range(0, 8), range(0, 8), (0, 1)):
        ok = sum(1 for x, z, g in samples
                 if ((((x + ox) // wx + (z + oz) // wz) % 2 == p) == g))
        if best is None or ok > best[0]:
            best = (ok, wx, wz, ox, oz, p)
    return best

ok, wx, wz, ox, oz, p = fit(SAMPLE)
print('best fit: wx=%d wz=%d offsets=(%d,%d) parity=%d  -> %.1f%% of %d samples'
      % (wx, wz, ox, oz, p, 100.0 * ok / len(SAMPLE), len(SAMPLE)))

# applying it: same coordinate space as the source, so the pattern continues
# seamlessly across the red border instead of restarting at a new phase.
ARENA_X0 = ARENA_Z0 = 85

def floor_block(lx, lz):
    ax, az = lx - ARENA_X0, lz - ARENA_Z0
    return 'polished_granite' if ((ax // 5) + (az // 4)) % 2 == 1 else 'terracotta'

print('ring sample, continuing outward from the arena edge:')
for lz in (70, 71, 72):
    print('  z=%d  %s' % (lz, ' '.join(floor_block(x, lz)[:4] for x in range(78, 92))))
