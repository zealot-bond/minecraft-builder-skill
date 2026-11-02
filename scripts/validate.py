#!/usr/bin/env python3
"""Validate a structure NBT before it ever reaches a server.

This encodes every defect that caused a real build to be rejected. It exits
non-zero if anything fails, so a build pipeline can gate on it.

    validate.py out.nbt
    validate.py out.nbt --floor 31 --flat 40 40 229 229 --max-jump 3 \
                --outdir renders --strict

Each check prints PASS / FAIL / SKIP with the measured number. "SKIP" is used when
the check needs information you did not supply -- it is never reported as a pass.
"""
import sys, os, gzip, struct, argparse
from collections import Counter, deque

N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))

# ---------------------------------------------------------------- NBT reading
def read_nbt(raw, i=0):
    t = raw[i]; i += 1
    if t == 0:
        return None, i
    nl = struct.unpack_from('>H', raw, i)[0]; i += 2
    name = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
    v, i = payload(raw, i, t)
    return (name, v), i


def payload(raw, i, t):
    if t == 1: return struct.unpack_from('>b', raw, i)[0], i + 1
    if t == 2: return struct.unpack_from('>h', raw, i)[0], i + 2
    if t == 3: return struct.unpack_from('>i', raw, i)[0], i + 4
    if t == 4: return struct.unpack_from('>q', raw, i)[0], i + 8
    if t == 5: return struct.unpack_from('>f', raw, i)[0], i + 4
    if t == 6: return struct.unpack_from('>d', raw, i)[0], i + 8
    if t == 7:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return raw[i:i + n], i + n
    if t == 8:
        n = struct.unpack_from('>H', raw, i)[0]; i += 2
        return raw[i:i + n].decode('utf-8', 'replace'), i + n
    if t == 9:
        et = raw[i]; n = struct.unpack_from('>i', raw, i + 1)[0]; i += 5
        out = []
        for _ in range(n):
            v, i = payload(raw, i, et); out.append(v)
        return out, i
    if t == 10:
        out = {}
        while True:
            tt = raw[i]; i += 1
            if tt == 0: break
            nl = struct.unpack_from('>H', raw, i)[0]; i += 2
            nm = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
            v, i = payload(raw, i, tt); out[nm] = v
        return out, i
    if t == 11:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>i', raw, i + 4 * k)[0] for k in range(n)], i + 4 * n
    if t == 12:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>q', raw, i + 8 * k)[0] for k in range(n)], i + 8 * n
    raise ValueError('bad tag %d' % t)


def load(path):
    with gzip.open(path, 'rb') as f:
        raw = f.read()
    (name, root), i = read_nbt(raw, 0)
    return root, len(raw) - i


# Blocks that are not "terrain" for the purpose of a surface-height check. A tree
# standing on a terrace must not count as a 20-block discontinuity of the terrace.
# ---------------------------------------------------------------- block families
LEAVES = lambda b: b.endswith('_leaves')
LOGS = lambda b: b.endswith(('_log', '_wood', '_stem', '_hyphae'))
FOLIAGE = lambda b: LEAVES(b) or LOGS(b)
SOILS = {'grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'moss_block',
         'podzol', 'mycelium', 'farmland', 'mud'}
FLAT_PLANTS = {
    'short_grass', 'tall_grass', 'fern', 'large_fern', 'poppy', 'dandelion',
    'red_tulip', 'orange_tulip', 'white_tulip', 'pink_tulip', 'blue_orchid',
    'allium', 'azure_bluet', 'oxeye_daisy', 'cornflower', 'lily_of_the_valley',
    'pink_petals', 'moss_carpet', 'small_dripleaf', 'torchflower', 'carrots',
    'potatoes', 'wheat', 'beetroots', 'sweet_berry_bush', 'sea_pickle',
    'sugar_cane', 'kelp', 'lily_pad', 'vine', 'glow_lichen', 'snow',
}
# Blocks that cannot hold anything up. SOILS are NOT here on purpose: a tree
# standing on grass is grounded, and putting dirt in this set made every tree in
# the build report as floating.
NO_SUPPORT = {
    'air', 'cave_air', 'void_air', 'water', 'lava',
    'iron_chain', 'lantern', 'scaffolding', 'ladder', 'tripwire',
    'light', 'barrier',
} | FLAT_PLANTS


def is_terrain(v):
    """True if this block is part of the ground, for surface-height checks."""
    if v in ('air', 'cave_air', 'void_air', 'water', 'lava'):
        return False
    if FOLIAGE(v) or v in FLAT_PLANTS:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nbt')
    ap.add_argument('--floor', type=int, help='build ly of the flat surface')
    ap.add_argument('--flat', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'),
                    help='flat area rectangle in local coords')
    ap.add_argument('--blend', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'),
                    help='region whose surface must be continuous')
    ap.add_argument('--max-jump', type=int, default=3)
    ap.add_argument('--allow-water', action='store_true')
    ap.add_argument('--allow-tripwire', action='store_true')
    ap.add_argument('--allow-openings', nargs='*', default=[],
                    metavar='X,Z', help='columns allowed to be open (shafts)')
    ap.add_argument('--exclude', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'),
                    help='ignore this rectangle in the holes/continuity checks '
                         '(e.g. an arena full of buildings)')
    ap.add_argument('--strict', action='store_true', help='SKIP counts as failure')
    a = ap.parse_args()

    root, leftover = load(a.nbt)
    size = tuple(root['size'])
    pal = root['palette']
    blocks = root['blocks']
    nx, ny, nz = size

    def nm(entry):
        return (entry.get('Name') if isinstance(entry, dict) else entry).split(':')[-1]

    def props(entry):
        if isinstance(entry, dict) and entry.get('Properties'):
            return dict(entry['Properties'])
        return {}

    results = []

    def check(name, ok, detail):
        results.append((name, ok, detail))
        print('%-22s %-4s %s' % (name, 'PASS' if ok else 'FAIL', detail))

    def skip(name, why):
        results.append((name, None, why))
        print('%-22s %-4s %s' % (name, 'SKIP', why))

    print('== %s ==' % a.nbt)
    print('size %dx%dx%d  palette %d  blocks %d' % (nx, ny, nz, len(pal), len(blocks)))
    print()

    # 1 file integrity
    check('file.roundtrip', leftover == 0,
          'trailing bytes=%d' % leftover)

    # 2 palette
    check('palette.air0', nm(pal[0]) == 'air', 'palette[0]=%s' % nm(pal[0]))
    dup = len(pal) - len({(nm(e), tuple(sorted(props(e).items()))) for e in pal})
    check('palette.unique', dup == 0, 'duplicate states=%d' % dup)

    # 3 bounds
    oob = 0
    for b in blocks:
        x, y, z = b['pos']
        if not (0 <= x < nx and 0 <= y < ny and 0 <= z < nz):
            oob += 1
    check('bounds', oob == 0, 'out-of-bounds=%d' % oob)

    # index for geometry checks
    at = {}
    for b in blocks:
        at[(b['pos'][0], b['pos'][1], b['pos'][2])] = nm(pal[b['state']])

    def get(p):
        return at.get(p, 'air')

    # 4 water
    water = sum(1 for v in at.values() if v in ('water', 'lava'))
    if a.allow_water:
        skip('water', 'allowed by flag (%d blocks)' % water)
    else:
        check('water', water == 0, 'water/lava blocks=%d' % water)

    # 5 tripwire
    tw = sum(1 for v in at.values() if v == 'tripwire')
    if a.allow_tripwire:
        skip('tripwire', 'allowed by flag (%d)' % tw)
    else:
        check('tripwire', tw == 0, 'tripwire blocks=%d' % tw)

    # 6 plant support (below must be a support)
    bad_plant = 0
    for (x, y, z), v in at.items():
        if v not in FLAT_PLANTS:
            continue
        below = get((x, y - 1, z))
        if below in NO_SUPPORT:
            bad_plant += 1
    check('support.plants', bad_plant == 0, 'plants with no support=%d' % bad_plant)

    # 7 wall-mounted blocks need a solid backing in their facing direction
    FACING = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
    bad_wall = 0
    wall_total = 0
    for b in blocks:
        v = nm(pal[b['state']])
        if not (v.endswith('_wall_banner') or v.endswith('_wall_sign')
                or v.endswith('_wall_head') or v == 'player_wall_head'):
            continue
        wall_total += 1
        pr = props(pal[b['state']])
        dx, dz = FACING.get(pr.get('facing', 'north'), (0, -1))
        x, y, z = b['pos']
        back = get((x + dx, y, z + dz))
        if back in NO_SUPPORT or back.endswith(('banner', 'sign')):
            bad_wall += 1
    check('support.wall_mounted', bad_wall == 0,
          '%d wall blocks, unsupported=%d' % (wall_total, bad_wall))

    # 8 soil resting on foliage
    bad_soil = 0
    for (x, y, z), v in at.items():
        if v in SOILS and FOLIAGE(get((x, y - 1, z))):
            bad_soil += 1
    check('trees.soil_on_logs', bad_soil == 0,
          'soil blocks resting on logs/leaves=%d' % bad_soil)

    # 9 floating foliage: a foliage component is grounded only if some member sits
    #    on a non-foliage, non-plant block.
    seen = set()
    grounded = floating = 0
    floating_blocks = 0
    for p, v in list(at.items()):
        if not FOLIAGE(v) or p in seen:
            continue
        q = deque([p]); seen.add(p); comp = []
        while q:
            cur = q.popleft(); comp.append(cur)
            for d in N6:
                nb = (cur[0] + d[0], cur[1] + d[1], cur[2] + d[2])
                if nb in seen:
                    continue
                nv = at.get(nb)
                if nv is None or not FOLIAGE(nv):
                    continue
                seen.add(nb); q.append(nb)
        ok = False
        for (x, y, z) in comp:
            below = get((x, y - 1, z))
            if below not in NO_SUPPORT and not FOLIAGE(below):
                ok = True
                break
        if ok:
            grounded += 1
        else:
            floating += 1
            floating_blocks += len(comp)
    check('trees.floating', floating == 0,
          '%d components: %d grounded, %d floating (%d blocks)'
          % (grounded + floating, grounded, floating, floating_blocks))

    # 10 flatness / holes
    if a.floor is None or a.flat is None:
        skip('surface.holes', 'needs --floor and --flat')
    else:
        x0, z0, x1, z1 = a.flat
        allowed = set()
        for spec in a.allow_openings:
            cx, cz, r = (spec.split(',') + ['2'])[:3]
            for dx in range(-int(r), int(r) + 1):
                for dz in range(-int(r), int(r) + 1):
                    allowed.add((int(cx) + dx, int(cz) + dz))
        ex = a.exclude
        holes = 0
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if (x, z) in allowed:
                    continue
                if ex and ex[0] <= x <= ex[2] and ex[1] <= z <= ex[3]:
                    continue
                if get((x, a.floor, z)) == 'air':
                    holes += 1
        check('surface.holes', holes == 0, 'open columns at floor=%d' % holes)

    # 11 continuity of the surface height across the blend region
    if a.blend is None:
        skip('surface.continuity', 'needs --blend')
    else:
        x0, z0, x1, z1 = a.blend
        top = {}
        ex = a.exclude
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if ex and ex[0] <= x <= ex[2] and ex[1] <= z <= ex[3]:
                    continue
                hi = None
                for y in range(ny - 1, -1, -1):
                    v = at.get((x, y, z))
                    if v is not None and is_terrain(v):
                        hi = y
                        break
                top[(x, z)] = hi
        worst = 0
        worst_at = None
        for (x, z), h in top.items():
            if h is None:
                continue
            for dx, dz in ((1, 0), (0, 1), (1, 1)):
                n = top.get((x + dx, z + dz))
                if n is None:
                    continue
                d = abs(h - n)
                if d > worst:
                    worst = d; worst_at = (x, z)
        check('surface.continuity', worst <= a.max_jump,
              'max adjacent jump=%d at %s (limit %d)' % (worst, worst_at, a.max_jump))

    # ---- summary
    failed = [r for r in results if r[1] is False]
    skipped = [r for r in results if r[1] is None]
    print()
    print('%d checks: %d passed, %d failed, %d skipped'
          % (len(results), len(results) - len(failed) - len(skipped),
             len(failed), len(skipped)))
    if failed:
        print('FAILED: ' + ', '.join(r[0] for r in failed))
        return 1
    if skipped and a.strict:
        print('STRICT: skipped checks count as failure: '
              + ', '.join(r[0] for r in skipped))
        return 1
    print('OK — safe to upload and paste')
    return 0


if __name__ == '__main__':
    sys.exit(main())
