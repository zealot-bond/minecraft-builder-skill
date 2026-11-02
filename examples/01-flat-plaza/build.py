#!/usr/bin/env python3
"""Example 01 - the smallest correct build: one flat plaza and a border ring.

Teaches: palette grid, explicit air at index 0, one flat surface, writing NBT.
Run:  python3 build.py   ->  flat-plaza.nbt
Then: python3 ../../scripts/validate.py flat-plaza.nbt --floor 8 --flat 2 2 45 45
"""
import os, sys
from array import array
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
import streamnbt

N, SY = 48, 20
FLOOR = 8                      # the one walkable level
PAL, IX = [], {}
M = 'minecraft:'


def pid(name, props=None):
    key = (name, tuple(sorted((props or {}).items())))
    if key not in IX:
        IX[key] = len(PAL); PAL.append(key)
    return IX[key]


AIR = pid(M + 'air')
assert AIR == 0, 'palette index 0 must be air'
GRASS = pid(M + 'grass_block', {'snowy': 'false'})
STONE = pid(M + 'stone')
POL = pid(M + 'polished_andesite')
BLUE = pid(M + 'blue_stained_glass')

G = array('H', bytes(2 * N * SY * N))


def I(x, y, z): return y * N * N + z * N + x


def put(x, y, z, v):
    if 0 <= x < N and 0 <= y < SY and 0 <= z < N:
        G[I(x, y, z)] = v


for z in range(N):
    for x in range(N):
        d = min(x, z, N - 1 - x, N - 1 - z)
        for y in range(FLOOR + 1):
            if y == FLOOR:
                put(x, y, z, BLUE if d == 0 else (POL if d == 1 else GRASS))
            else:
                put(x, y, z, STONE)

out = os.path.join(os.path.dirname(__file__), 'flat-plaza.nbt')
total = sum(1 for v in G if v)
pal_out = [(n, dict(p) if p else None) for n, p in PAL]


def emit():
    for y in range(SY):
        for z in range(N):
            for x in range(N):
                v = G[I(x, y, z)]
                if v:
                    yield (x, y, z, v)


size = streamnbt.write_structure(out, (N, SY, N), pal_out, total, emit())
print('%s  %d blocks  %.1f KB' % (out, total, size / 1024.0))
print('void if pasted = %d' % (N * SY * N - total))
