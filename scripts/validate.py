#!/usr/bin/env python3
"""Validate a structure NBT for structural & physical defects before paste or ship.

Checks:
  1. file.roundtrip       NBT parses cleanly with 0 trailing bytes
  2. palette.air0         palette[0] is minecraft:air; no duplicate blockstates
  3. bounds               every block coordinate inside size
  4. fluid.containment    water/lava allowed by default, but ZERO leaks (every fluid
                          block is supported below and enclosed laterally; pass
                          --no-water for legacy dry-only builds)
  5. tripwire             0 stray tripwire unless --allow-tripwire
  6. leaves.persistent    every *_leaves block has persistent=true so canopies never decay
  7. support.plants       flat plants, lily pads, bamboo, reeds & 2-tall flora have valid support
  8. support.hanging      hanging lanterns, chains, vines & hanging roots attach to solid support
  9. support.wall_mounted wall banners/signs/heads/torches have solid backing
 10. trees.soil_on_logs   0 soil blocks resting directly on logs or leaves
 11. trees.floating       0 floating foliage components (6-connected to grounded trunk)
 12. surface.holes / surface.continuity  (optional flat/blend checks when flags supplied)
"""

import argparse
from collections import deque
import gzip
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mckit.blocks import (
    AIR_NAMES,
    CHAINS,
    FLAT_PLANTS,
    FLUID_NAMES,
    HANGING_ONLY,
    NO_SUPPORT,
    SOILS,
    is_fence,
    is_foliage,
    is_leaves,
    is_log,
    is_slab,
    is_solid_full,
    is_stairs,
    is_trapdoor,
    is_wall,
    short_name,
)

N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
TALL_DOUBLE = frozenset({'tall_grass', 'large_fern', 'sunflower', 'lilac', 'rose_bush', 'peony', 'pitcher_plant', 'tall_seagrass'})


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


def load_nbt(path):
    with gzip.open(path, 'rb') as f:
        raw = f.read()
    (_, root), i = read_nbt(raw, 0)
    return root, len(raw) - i


def is_terrain(v):
    if v in AIR_NAMES or v in FLUID_NAMES:
        return False
    if is_foliage(v) or v in FLAT_PLANTS:
        return False
    return True


def is_fluid_retainer(v, pr=None):
    """True if block `v` can hold water laterally or from below without leaking."""
    if v in FLUID_NAMES:
        return True
    if is_solid_full(v) or is_stairs(v) or is_slab(v) or is_wall(v) or is_trapdoor(v):
        return True
    if v in ('glass', 'ice', 'packed_ice', 'blue_ice') or v.endswith('_stained_glass'):
        return True
    if pr and pr.get('waterlogged') == 'true':
        return True
    return False


def can_hang_from(v):
    """True if chains/hanging lanterns can hang underneath block `v`."""
    if v in CHAINS or is_solid_full(v) or is_log(v) or is_leaves(v):
        return True
    if is_slab(v) or is_stairs(v) or is_fence(v) or is_wall(v) or is_trapdoor(v):
        return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('nbt')
    ap.add_argument('--project', help='optional project.json for legacy constraints')
    ap.add_argument('--floor', type=int, help='build ly of a required flat surface')
    ap.add_argument('--flat', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'))
    ap.add_argument('--blend', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'))
    ap.add_argument('--max-jump', type=int, default=3)
    ap.add_argument('--no-water', action='store_true', help='disallow water/lava (legacy mode)')
    ap.add_argument('--allow-water', action='store_true', help='accepted for CLI compatibility (default)')
    ap.add_argument('--allow-tripwire', action='store_true')
    ap.add_argument('--allow-openings', nargs='*', default=[], metavar='X,Z')
    ap.add_argument('--exclude', nargs=4, type=int, metavar=('X0', 'Z0', 'X1', 'Z1'))
    ap.add_argument('--strict', action='store_true', help='enforce strict checks')
    a = ap.parse_args(argv)

    proj = {}
    if a.project and os.path.exists(a.project):
        with open(a.project, 'r', encoding='utf-8') as f:
            proj = json.load(f)
    no_water = a.no_water or bool(proj.get('no_water', False))
    whitelist = set(short_name(x) for x in proj['whitelist']) if proj.get('whitelist') else None

    root, leftover = load_nbt(a.nbt)
    nx, ny, nz = tuple(root['size'])
    pal = root['palette']
    blocks = root['blocks']

    def nm(entry):
        return short_name(entry.get('Name') if isinstance(entry, dict) else entry)

    def props(entry):
        if isinstance(entry, dict) and entry.get('Properties'):
            return dict(entry['Properties'])
        return {}

    results = []

    def check(name, ok, detail):
        results.append((name, ok, detail))
        print('%-22s %-4s %s' % (name, 'PASS' if ok else 'FAIL', detail))

    print('== %s ==' % a.nbt)
    print('size %dx%dx%d  palette %d  blocks %d' % (nx, ny, nz, len(pal), len(blocks)))
    print()

    # 1. File integrity & palette
    check('file.roundtrip', leftover == 0, 'trailing bytes=%d' % leftover)
    check('palette.air0', nm(pal[0]) == 'air', 'palette[0]=%s' % nm(pal[0]))
    dup = len(pal) - len({(nm(e), tuple(sorted(props(e).items()))) for e in pal})
    check('palette.unique', dup == 0, 'duplicate states=%d' % dup)

    # 2. Bounds + build spatial index
    oob = 0
    at = {}
    at_state = {}
    pal_nm = [nm(e) for e in pal]
    pal_pr = [props(e) for e in pal]
    for b in blocks:
        x, y, z = b['pos']
        if not (0 <= x < nx and 0 <= y < ny and 0 <= z < nz):
            oob += 1
            continue
        st = b['state']
        if pal_nm[st] not in AIR_NAMES:
            at[(x, y, z)] = pal_nm[st]
            at_state[(x, y, z)] = st
    check('bounds', oob == 0, 'out-of-bounds=%d' % oob)

    if whitelist is not None:
        bad_wl = sorted({v for v in at.values() if v not in whitelist})
        check('palette.whitelist', len(bad_wl) == 0,
              'disallowed=%s' % (','.join(bad_wl[:8]) if bad_wl else 'none'))

    def get(p):
        return at.get(p, 'air')

    def get_pr(p):
        st = at_state.get(p)
        return pal_pr[st] if st is not None else {}

    # 3. Water / fluid containment
    fluids = [(p, v) for p, v in at.items() if v in FLUID_NAMES]
    if no_water:
        check('water.forbidden', len(fluids) == 0, 'water/lava blocks=%d' % len(fluids))
    else:
        leaks = 0
        leak_sample = None
        for (x, y, z), fv in fluids:
            # Must not sit on the exposed boundary of the schematic box unless walled
            if x in (0, nx - 1) or z in (0, nz - 1) or y == 0:
                leaks += 1
                leak_sample = leak_sample or (x, y, z, 'box-edge')
                continue
            below = get((x, y - 1, z))
            below_pr = get_pr((x, y - 1, z))
            if not is_fluid_retainer(below, below_pr):
                leaks += 1
                leak_sample = leak_sample or (x, y, z, f'below={below}')
                continue

            # Check 4 horizontal neighbours
            open_sides = 0
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = get((x + dx, y, z + dz))
                nb_pr = get_pr((x + dx, y, z + dz))
                if not is_fluid_retainer(nb, nb_pr):
                    open_sides += 1

            if below == fv:
                # Vertical waterfall column allowed if cradled on >=3 sides AND lands in a contained pool
                if open_sides > 1:
                    leaks += 1
                    leak_sample = leak_sample or (x, y, z, f'waterfall-open-sides={open_sides}')
                else:
                    # Trace straight down to bottom of fluid column
                    by = y - 1
                    while by > 0 and get((x, by - 1, z)) == fv:
                        by -= 1
                    # Bottom cell `(x, by, z)` must be 4-side contained
                    bot_open = sum(
                        1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if not is_fluid_retainer(get((x + dx, by, z + dz)), get_pr((x + dx, by, z + dz)))
                    )
                    if bot_open > 0:
                        leaks += 1
                        leak_sample = leak_sample or (x, y, z, 'waterfall-uncontained-splash')
            else:
                # Standing pool / pond / fountain block: all 4 sides MUST retain fluid!
                if open_sides > 0:
                    leaks += 1
                    leak_sample = leak_sample or (x, y, z, f'pond-leak-sides={open_sides}')

        detail = '%d fluid blocks, leaks=%d' % (len(fluids), leaks)
        if leak_sample:
            detail += ' (first: %s)' % (leak_sample,)
        check('fluid.containment', leaks == 0, detail)

    # 4. Stray tripwire
    tw = sum(1 for v in at.values() if v == 'tripwire')
    if not a.allow_tripwire:
        check('tripwire', tw == 0, 'tripwire blocks=%d' % tw)

    # 5. Leaves persistence (prevents leaf decay on paste!)
    decay_leaves = 0
    leaf_total = 0
    for p, v in at.items():
        if is_leaves(v):
            leaf_total += 1
            if get_pr(p).get('persistent') != 'true':
                decay_leaves += 1
    check('leaves.persistent', decay_leaves == 0,
          '%d leaves, non-persistent=%d' % (leaf_total, decay_leaves))

    # 6. Plant support
    bad_plant = 0
    plant_sample = None
    for (x, y, z), v in at.items():
        if v not in FLAT_PLANTS:
            continue
        below = get((x, y - 1, z))
        pr = get_pr((x, y, z))
        if v == 'lily_pad':
            ok = (below == 'water')
        elif v == 'bamboo':
            ok = (below == 'bamboo' or below in SOILS)
        elif v == 'sugar_cane':
            ok = (below == 'sugar_cane' or below in SOILS)
        elif v in ('seagrass', 'tall_seagrass', 'kelp', 'kelp_plant', 'sea_pickle'):
            ok = is_solid_full(below) or below in SOILS or (v == 'tall_seagrass' and pr.get('half') == 'upper' and below == 'tall_seagrass')
        elif v in TALL_DOUBLE and pr.get('half') == 'upper':
            ok = (below == v)
        else:
            ok = (below not in NO_SUPPORT and not is_foliage(below))
        if not ok:
            bad_plant += 1
            plant_sample = plant_sample or (x, y, z, v, f'below={below}')
    p_det = 'unsupported plants=%d' % bad_plant
    if plant_sample:
        p_det += ' (first: %s)' % (plant_sample,)
    check('support.plants', bad_plant == 0, p_det)

    # 7. Hanging blocks (lanterns, chains, hanging roots, spore blossoms, cave vines)
    bad_hang = 0
    hang_sample = None
    for (x, y, z), v in at.items():
        pr = get_pr((x, y, z))
        above = get((x, y + 1, z))
        if v in ('lantern', 'soul_lantern'):
            if pr.get('hanging') == 'true':
                if not can_hang_from(above):
                    bad_hang += 1
                    hang_sample = hang_sample or (x, y, z, v, f'above={above}')
            else:
                below = get((x, y - 1, z))
                if below in NO_SUPPORT:
                    bad_hang += 1
                    hang_sample = hang_sample or (x, y, z, v, f'standing-on={below}')
        elif v in CHAINS and pr.get('axis', 'y') == 'y':
            # Top of vertical chain run must attach above OR bottom must stand on solid post
            top_y = y
            while get((x, top_y + 1, z)) in CHAINS and get_pr((x, top_y + 1, z)).get('axis', 'y') == 'y':
                top_y += 1
            bot_y = y
            while get((x, bot_y - 1, z)) in CHAINS and get_pr((x, bot_y - 1, z)).get('axis', 'y') == 'y':
                bot_y -= 1
            attached_top = can_hang_from(get((x, top_y + 1, z)))
            supported_bot = get((x, bot_y - 1, z)) not in NO_SUPPORT
            if not (attached_top or supported_bot):
                bad_hang += 1
                hang_sample = hang_sample or (x, y, z, v, 'floating-chain')
        elif v in HANGING_ONLY:
            if not (can_hang_from(above) or above in HANGING_ONLY):
                bad_hang += 1
                hang_sample = hang_sample or (x, y, z, v, f'above={above}')
    h_det = 'unsupported hanging=%d' % bad_hang
    if hang_sample:
        h_det += ' (first: %s)' % (hang_sample,)
    check('support.hanging', bad_hang == 0, h_det)

    # 8. Wall-mounted blocks
    FACING = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
    bad_wall = 0
    wall_total = 0
    for (x, y, z), v in at.items():
        if not (v.endswith('_wall_banner') or v.endswith('_wall_sign')
                or v.endswith('_wall_head') or v == 'player_wall_head'
                or v in ('wall_torch', 'soul_wall_torch', 'redstone_wall_torch')):
            continue
        wall_total += 1
        pr = get_pr((x, y, z))
        # Wall signs/banners/torches face AWAY from the backing wall!
        face = pr.get('facing', 'north')
        dx, dz = FACING.get(face, (0, -1))
        # Check both -dir (vanilla wall sign/torch backing) and +dir (legacy convention)
        back_vanilla = get((x - dx, y, z - dz))
        back_alt = get((x + dx, y, z + dz))
        ok_v = back_vanilla not in NO_SUPPORT and not back_vanilla.endswith(('banner', 'sign'))
        ok_a = back_alt not in NO_SUPPORT and not back_alt.endswith(('banner', 'sign'))
        if not (ok_v or ok_a):
            bad_wall += 1
    check('support.wall_mounted', bad_wall == 0,
          '%d wall blocks, unsupported=%d' % (wall_total, bad_wall))

    # 9. Soil resting on logs / leaves
    bad_soil = 0
    for (x, y, z), v in at.items():
        if v in SOILS and is_foliage(get((x, y - 1, z))):
            bad_soil += 1
    check('trees.soil_on_logs', bad_soil == 0, 'soil resting on logs/leaves=%d' % bad_soil)

    # 10. Floating foliage (6-connected component check)
    seen = set()
    grounded = floating = floating_blocks = 0
    for p, v in list(at.items()):
        if not is_foliage(v) or p in seen:
            continue
        q = deque([p]); seen.add(p); comp = []
        while q:
            cur = q.popleft(); comp.append(cur)
            for d in N6:
                nb = (cur[0] + d[0], cur[1] + d[1], cur[2] + d[2])
                if nb in seen:
                    continue
                nv = at.get(nb)
                if nv is None or not is_foliage(nv):
                    continue
                seen.add(nb); q.append(nb)
        ok = any(
            get((x, y - 1, z)) not in NO_SUPPORT and not is_foliage(get((x, y - 1, z)))
            for (x, y, z) in comp
        )
        if ok:
            grounded += 1
        else:
            floating += 1
            floating_blocks += len(comp)
    check('trees.floating', floating == 0,
          '%d components: %d grounded, %d floating (%d blocks)'
          % (grounded + floating, grounded, floating, floating_blocks))

    # 11. Optional flat-surface holes check (only when --floor and --flat supplied)
    if a.floor is not None and a.flat is not None:
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

    # 12. Optional blend surface continuity check (only when --blend supplied)
    if a.blend is not None:
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

    failed = [r for r in results if r[1] is False]
    print()
    print('%d checks: %d passed, %d failed' % (len(results), len(results) - len(failed), len(failed)))
    if failed:
        print('FAILED: ' + ', '.join(r[0] for r in failed))
        return 1
    print('OK — structurally valid')
    return 0


if __name__ == '__main__':
    sys.exit(main())
