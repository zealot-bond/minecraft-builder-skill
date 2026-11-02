"""Organic custom tree generator with roots, tapered 6-connected limbs,
cloud-cluster canopies ("cluster & subtract"), mixed foliage, ground petal litter,
and guaranteed swing/lantern branch anchors.
"""

from collections import deque
import math
import random

from .blocks import FLAT_PLANTS, NO_SUPPORT, is_foliage, is_leaves, is_log, short_name
from .palette import mix, rand01
from .shapes import bezier_point, noise3d

_N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def _rng(seed, x, y, z):
    return random.Random((int(seed) * 7919) ^ (int(x) * 73856093) ^ (int(y) * 83492791) ^ (int(z) * 19349663))


def _step6(p0, p1):
    """Yield a strictly 6-connected voxel chain from integer 3D `p0` to `p1`."""
    x, y, z = int(round(p0[0])), int(round(p0[1])), int(round(p0[2]))
    tx, ty, tz = int(round(p1[0])), int(round(p1[1])), int(round(p1[2]))
    pts = [(x, y, z)]
    while (x, y, z) != (tx, ty, tz):
        dx, dy, dz = tx - x, ty - y, tz - z
        ax, ay, az = abs(dx), abs(dy), abs(dz)
        if ax >= ay and ax >= az:
            x += 1 if dx > 0 else -1
        elif ay >= ax and ay >= az:
            y += 1 if dy > 0 else -1
        else:
            z += 1 if dz > 0 else -1
        pts.append((x, y, z))
    return pts


def _spline_wood(wood_map, ctrl_pts, r0, r1, wood_block):
    """Rasterize a tapering curved trunk/limb with guaranteed 6-connectivity."""
    steps = max(10, int(sum(math.dist(ctrl_pts[i], ctrl_pts[i + 1]) for i in range(len(ctrl_pts) - 1)) * 2.5))
    prev = None
    spine = []
    for i in range(steps + 1):
        t = i / float(steps)
        px, py, pz = bezier_point(ctrl_pts, t)
        r = r0 + (r1 - r0) * t
        cur = (int(round(px)), int(round(py)), int(round(pz)))
        if prev is not None and cur != prev:
            for q in _step6(prev, cur):
                wood_map[q] = wood_block
                spine.append(q)
        else:
            wood_map[cur] = wood_block
            spine.append(cur)
        prev = cur
        if r >= 0.72:
            ir = int(math.ceil(r))
            r2 = r * r
            for dy in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    for dx in range(-ir, ir + 1):
                        if dx * dx + dy * dy + dz * dz <= r2:
                            wood_map[(int(round(px)) + dx, int(round(py)) + dy, int(round(pz)) + dz)] = wood_block
    return spine


def _cloud_cluster(leaf_map, wood_map, cx, cy, cz, rx, ry, rz, leaf_picker, subtract=0.22, seed=0):
    """Place an airy pancake leaf cluster around `(cx, cy, cz)`, then subtract 20-25% outer leaves."""
    ix, iy, iz = int(math.ceil(rx + 1.5)), int(math.ceil(ry + 1.2)), int(math.ceil(rz + 1.5))
    cx, cy, cz = int(round(cx)), int(round(cy)), int(round(cz))
    # Ensure cluster center touches wood or gets bridged
    for dy in range(-iy, iy + 1):
        for dz in range(-iz, iz + 1):
            for dx in range(-ix, ix + 1):
                x, y, z = cx + dx, cy + dy, cz + dz
                wob = noise3d(x, y, z, scale=2.8, seed=seed) * 0.28
                # Flatter bottom, puffier top like real builder cloud clusters
                vy = dy / float(max(0.8, ry * (1.15 if dy >= 0 else 0.75)))
                d = math.sqrt((dx / float(max(1.0, rx))) ** 2 + vy * vy + (dz / float(max(1.0, rz))) ** 2)
                if d <= 1.0 + wob:
                    if d > 0.52 and rand01(x, y, z, seed + 91) < subtract:
                        continue
                    if (x, y, z) not in wood_map:
                        leaf_map[(x, y, z)] = leaf_picker(x, y, z)


def _drape_leaves(leaf_map, wood_map, rnd, leaf_picker, max_drop=3, chance=0.18):
    """Hang trailing leaf curtains underneath outer canopy edges (sakura / willow style)."""
    candidates = [
        p for p in leaf_map
        if (p[0], p[1] - 1, p[2]) not in leaf_map and (p[0], p[1] - 1, p[2]) not in wood_map
    ]
    for x, y, z in candidates:
        if rnd.random() < chance:
            drop = rnd.randint(1, max_drop)
            for d in range(1, drop + 1):
                q = (x, y - d, z)
                if q in wood_map:
                    break
                leaf_map[q] = leaf_picker(x, y - d, z)


def _grow_roots(canvas, wood_map, x, y, z, wood_block, count, reach, rnd):
    """Spread asymmetric surface roots that step down cleanly to meet `ground_y`."""
    for i in range(count):
        ang = (2.0 * math.pi * i / float(count)) + rnd.uniform(-0.35, 0.35)
        ca, sa = math.cos(ang), math.sin(ang)
        length = rnd.uniform(reach * 0.7, reach * 1.15)
        prev = (x, y + rnd.randint(1, 2), z)
        wood_map[prev] = wood_block
        steps = max(3, int(round(length * 2.0)))
        for s in range(1, steps + 1):
            t = s / float(steps)
            rx = int(round(x + ca * length * t))
            rz = int(round(z + sa * length * t))
            if not (1 <= rx < canvas.sx - 1 and 1 <= rz < canvas.sz - 1):
                break
            gy = canvas.ground_y(rx, rz)
            if gy < 1 or canvas.get(rx, gy + 1, rz) == 'water':
                break
            ry = max(gy, int(round(y + (1.0 - t) * 1.8)))
            cur = (rx, ry, rz)
            for q in _step6(prev, cur):
                wood_map[q] = wood_block
            # Ground anchor column down to terrain so root never floats over a slope
            for yy in range(gy + 1, ry + 1):
                wood_map[(rx, yy, rz)] = wood_block
            prev = cur


def _add_swing_limb(canvas, wood_map, x, base_y, z, wood_block, rnd, preferred_dir=None):
    """Grow a sturdy horizontal limb suitable for hanging a 5-wide swing cleanly over walkable ground."""
    dirs = [(1, 0, 'z'), (-1, 0, 'z'), (0, 1, 'x'), (0, -1, 'x')]
    rnd.shuffle(dirs)
    if preferred_dir:
        dirs.sort(key=lambda d: 0 if (d[0], d[1]) == preferred_dir else 1)

    limb_y = base_y + rnd.randint(6, 8)
    for dx, dz, swing_axis in dirs:
        ax = x + dx * 5
        az = z + dz * 5
        if not (4 <= ax < canvas.sx - 4 and 4 <= az < canvas.sz - 4):
            continue
        gy = canvas.ground_y(ax, az)
        if gy < 2 or abs(gy - base_y) > 2:
            continue
        if canvas.get(ax, gy + 1, az) == 'water' or canvas.get(ax, gy, az) == 'water':
            continue
        # Check clearance along the 5-block swing span
        ok = True
        for o in range(-2, 3):
            sx_ = ax + (o if swing_axis == 'x' else 0)
            sz_ = az + (o if swing_axis == 'z' else 0)
            if canvas.ground_y(sx_, sz_) < 2 or canvas.get(sx_, canvas.top(sx_, sz_), sz_) == 'water':
                ok = False
                break
        if not ok:
            continue

        # Build horizontal branch from trunk `(x, limb_y, z)` out to `(ax + dx, limb_y, az + dz)`
        for step in range(0, 7):
            bx = x + dx * step
            bz = z + dz * step
            wood_map[(bx, limb_y, bz)] = wood_block
            if step <= 2:
                wood_map[(bx, limb_y - 1, bz)] = wood_block
        # Crossbar at `(ax, limb_y, az)` along `swing_axis` so BOTH chains at offset -2 and +2 hang directly under wood!
        for o in range(-2, 3):
            cx_ = ax + (o if swing_axis == 'x' else 0)
            cz_ = az + (o if swing_axis == 'z' else 0)
            wood_map[(cx_, limb_y, cz_)] = wood_block
        return {
            'pos': (ax, limb_y, az),
            'axis': swing_axis,
            'ground_y': gy,
            'drop': max(4, limb_y - (gy + 2)),
        }
    return None


def _prune_6connected(canvas, wood_map, leaf_map):
    """Keep ONLY wood and leaves 6-connected to a wood block resting directly on solid ground."""
    all_foliage = set(wood_map) | set(leaf_map)
    seeds = []
    for x, y, z in wood_map:
        if not canvas.in_bounds(x, y, z):
            continue
        below = canvas.get(x, y - 1, z)
        if below not in NO_SUPPORT and not is_foliage(below):
            seeds.append((x, y, z))
    keep = set(seeds)
    q = deque(seeds)
    while q:
        cx, cy, cz = q.popleft()
        for dx, dy, dz in _N6:
            nb = (cx + dx, cy + dy, cz + dz)
            if nb in all_foliage and nb not in keep and canvas.in_bounds(*nb):
                # Never replace existing water or place foliage below y=1
                if canvas.get(*nb) == 'water':
                    continue
                keep.add(nb)
                q.append(nb)
    wood_out = {p: v for p, v in wood_map.items() if p in keep}
    leaf_out = {p: v for p, v in leaf_map.items() if p in keep and p not in wood_out}
    return wood_out, leaf_out


# ------------------------------------------------------------ species builders
def _build_sakura(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'cherry_wood'
    leaves = mix([('cherry_leaves', 76), ('flowering_azalea_leaves', 16), ('pink_leaves_alt', 0)], seed=seed)
    leaf_pick = mix([('cherry_leaves', 80), ('flowering_azalea_leaves', 20)], seed=seed)
    wood_map, leaf_map = {}, {}

    H = max(9, int(round(rnd.randint(11, 14) * scale)))
    lean_ang = rnd.uniform(0, 2 * math.pi)
    lean_r = rnd.uniform(1.8, 3.4) * scale
    top_x = x + math.cos(lean_ang) * lean_r
    top_z = z + math.sin(lean_ang) * lean_r
    mid_x = x + math.cos(lean_ang + 0.4) * lean_r * 0.45
    mid_z = z + math.sin(lean_ang + 0.4) * lean_r * 0.45

    _spline_wood(wood_map, [(x, y, z), (mid_x, y + H * 0.45, mid_z), (top_x, y + H, top_z)],
                 0.95 * scale, 0.48, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=rnd.randint(3, 4), reach=2.6 * scale, rnd=rnd)

    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    # 5 sweeping umbrella limbs
    n_limbs = 5
    tips = [(top_x, y + H + 1, top_z)]
    for i in range(n_limbs):
        ang = (2 * math.pi * i / n_limbs) + rnd.uniform(-0.3, 0.3)
        start_h = y + int(H * rnd.uniform(0.58, 0.85))
        sx_ = x + (top_x - x) * ((start_h - y) / float(H))
        sz_ = z + (top_z - z) * ((start_h - y) / float(H))
        reach = rnd.uniform(3.2, 5.0) * scale
        rise = rnd.uniform(1.4, 3.0) * scale
        tx = sx_ + math.cos(ang) * reach
        tz = sz_ + math.sin(ang) * reach
        ty = start_h + rise
        mx = sx_ + math.cos(ang) * reach * 0.55
        mz = sz_ + math.sin(ang) * reach * 0.55
        my = start_h + rise * 0.75
        _spline_wood(wood_map, [(sx_, start_h, sz_), (mx, my, mz), (tx, ty, tz)], 0.62, 0.4, wood)
        tips.append((tx, ty, tz))

    if swing:
        sx_, sy_, sz_ = swing['pos']
        tips.append((sx_, sy_ + 2, sz_))

    for idx, (tx, ty, tz) in enumerate(tips):
        rx = rnd.uniform(2.6, 3.6) * scale
        ry = rnd.uniform(1.5, 2.1) * scale
        _cloud_cluster(leaf_map, wood_map, tx, ty + 1, tz, rx, ry, rx * 0.92,
                       leaf_pick, subtract=0.25, seed=seed + idx * 37)

    _drape_leaves(leaf_map, wood_map, rnd, leaf_pick, max_drop=2, chance=0.16)
    return wood_map, leaf_map, swing, 'pink_petals'


def _build_giant_oak(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'oak_wood'
    leaf_pick = mix([('oak_leaves', 68), ('azalea_leaves', 22), ('flowering_azalea_leaves', 10)], seed=seed)
    wood_map, leaf_map = {}, {}

    H = max(10, int(round(rnd.randint(13, 17) * scale)))
    _spline_wood(wood_map, [(x, y, z), (x + rnd.uniform(-1.2, 1.2), y + H * 0.5, z + rnd.uniform(-1.2, 1.2)),
                            (x + rnd.uniform(-1.5, 1.5), y + H, z + rnd.uniform(-1.5, 1.5))],
                 1.45 * scale, 0.6, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=5, reach=3.6 * scale, rnd=rnd)
    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    tips = [(x, y + H + 1, z)]
    for i in range(6):
        ang = (2 * math.pi * i / 6.0) + rnd.uniform(-0.28, 0.28)
        sh = y + int(H * rnd.uniform(0.52, 0.82))
        reach = rnd.uniform(4.5, 7.0) * scale
        rise = rnd.uniform(2.0, 4.2) * scale
        tx, ty, tz = x + math.cos(ang) * reach, sh + rise, z + math.sin(ang) * reach
        _spline_wood(wood_map, [(x, sh, z), ((x + tx) / 2, sh + rise * 0.7, (z + tz) / 2), (tx, ty, tz)],
                     0.8, 0.4, wood)
        tips.append((tx, ty, tz))

    if swing:
        sx_, sy_, sz_ = swing['pos']
        tips.append((sx_, sy_ + 2, sz_))

    for idx, (tx, ty, tz) in enumerate(tips):
        _cloud_cluster(leaf_map, wood_map, tx, ty + 1, tz,
                       rnd.uniform(3.6, 5.0) * scale, rnd.uniform(2.2, 3.0) * scale, rnd.uniform(3.6, 5.0) * scale,
                       leaf_pick, subtract=0.22, seed=seed + idx * 41)
    _drape_leaves(leaf_map, wood_map, rnd, leaf_pick, max_drop=2, chance=0.12)
    return wood_map, leaf_map, swing, 'moss_carpet'


def _build_weeping_willow(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'oak_wood'
    leaf_pick = mix([('oak_leaves', 55), ('azalea_leaves', 35), ('mangrove_leaves', 10)], seed=seed)
    wood_map, leaf_map = {}, {}

    H = max(10, int(round(rnd.randint(12, 15) * scale)))
    lean_a = rnd.uniform(0, 2 * math.pi)
    tx0, tz0 = x + math.cos(lean_a) * 2.5, z + math.sin(lean_a) * 2.5
    _spline_wood(wood_map, [(x, y, z), (x + math.cos(lean_a) * 1.4, y + H * 0.5, z + math.sin(lean_a) * 1.4),
                            (tx0, y + H, tz0)], 1.2 * scale, 0.5, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=4, reach=3.0 * scale, rnd=rnd)
    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    tips = [(tx0, y + H, tz0)]
    for i in range(6):
        ang = (2 * math.pi * i / 6.0) + rnd.uniform(-0.25, 0.25)
        sh = y + int(H * rnd.uniform(0.65, 0.9))
        reach = rnd.uniform(4.0, 6.2) * scale
        # Arching up then drooping slightly at tip
        mx, my, mz = tx0 + math.cos(ang) * reach * 0.55, sh + 2.5, tz0 + math.sin(ang) * reach * 0.55
        bx, by, bz = tx0 + math.cos(ang) * reach, sh + 0.5, tz0 + math.sin(ang) * reach
        _spline_wood(wood_map, [(tx0, sh, tz0), (mx, my, mz), (bx, by, bz)], 0.65, 0.4, wood)
        tips.append((bx, by, bz))

    for idx, (tx, ty, tz) in enumerate(tips):
        _cloud_cluster(leaf_map, wood_map, tx, ty + 1, tz,
                       3.5 * scale, 2.0 * scale, 3.5 * scale, leaf_pick, subtract=0.18, seed=seed + idx * 29)
    # Signature long willow curtains!
    _drape_leaves(leaf_map, wood_map, rnd, leaf_pick, max_drop=5, chance=0.38)
    return wood_map, leaf_map, swing, 'moss_carpet'


def _build_japanese_pine(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'dark_oak_wood'
    leaf_pick = mix([('spruce_leaves', 70), ('dark_oak_leaves', 30)], seed=seed)
    wood_map, leaf_map = {}, {}

    H = max(9, int(round(rnd.randint(11, 15) * scale)))
    ang0 = rnd.uniform(0, 2 * math.pi)
    # Windswept S-curve bonsai pine silhouette
    p1 = (x + math.cos(ang0) * 3.0 * scale, y + H * 0.42, z + math.sin(ang0) * 3.0 * scale)
    p2 = (x - math.cos(ang0) * 1.5 * scale, y + H, z - math.sin(ang0) * 1.5 * scale)
    _spline_wood(wood_map, [(x, y, z), p1, p2], 1.15 * scale, 0.45, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=4, reach=2.8 * scale, rnd=rnd)
    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    # Flat horizontal bonsai cloud pads at distinct tiers
    pads = [(p2[0], p2[1] + 1, p2[2], 3.6 * scale)]
    for i in range(4):
        t = 0.42 + 0.14 * i
        bx, by, bz = bezier_point([(x, y, z), p1, p2], t)
        ang = ang0 + i * 1.85 + rnd.uniform(-0.25, 0.25)
        reach = rnd.uniform(3.2, 5.0) * scale
        tx, ty, tz = bx + math.cos(ang) * reach, by + rnd.uniform(0.3, 1.2), bz + math.sin(ang) * reach
        _spline_wood(wood_map, [(bx, by, bz), ((bx + tx) / 2, by + 0.5, (bz + tz) / 2), (tx, ty, tz)],
                     0.6, 0.4, wood)
        pads.append((tx, ty, tz, rnd.uniform(2.8, 3.8) * scale))

    for idx, (px, py, pz, pr) in enumerate(pads):
        _cloud_cluster(leaf_map, wood_map, px, py, pz, pr, 1.25, pr, leaf_pick, subtract=0.14, seed=seed + idx * 19)
    return wood_map, leaf_map, swing, 'moss_carpet'


def _build_autumn_maple(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'spruce_wood'
    leaf_pick = mix([('birch_leaves', 52), ('oak_leaves', 32), ('flowering_azalea_leaves', 16)], seed=seed)
    wood_map, leaf_map = {}, {}

    H = max(10, int(round(rnd.randint(12, 16) * scale)))
    _spline_wood(wood_map, [(x, y, z), (x + rnd.uniform(-1, 1), y + H * 0.55, z + rnd.uniform(-1, 1)),
                            (x, y + H, z)], 1.2 * scale, 0.5, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=4, reach=3.0 * scale, rnd=rnd)
    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    tips = [(x, y + H + 1, z)]
    for i in range(5):
        ang = (2 * math.pi * i / 5.0) + rnd.uniform(-0.3, 0.3)
        sh = y + int(H * rnd.uniform(0.5, 0.8))
        reach = rnd.uniform(3.5, 5.5) * scale
        rise = rnd.uniform(2.2, 4.0) * scale
        tx, ty, tz = x + math.cos(ang) * reach, sh + rise, z + math.sin(ang) * reach
        _spline_wood(wood_map, [(x, sh, z), (tx, ty, tz)], 0.65, 0.4, wood)
        tips.append((tx, ty, tz))

    for idx, (tx, ty, tz) in enumerate(tips):
        _cloud_cluster(leaf_map, wood_map, tx, ty + 1, tz,
                       3.4 * scale, 2.6 * scale, 3.4 * scale, leaf_pick, subtract=0.22, seed=seed + idx * 53)
    return wood_map, leaf_map, swing, 'moss_carpet'


def _build_birch_grove(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'birch_wood'
    leaf_pick = mix([('birch_leaves', 72), ('azalea_leaves', 28)], seed=seed)
    wood_map, leaf_map = {}, {}
    H = max(11, int(round(rnd.randint(13, 17) * scale)))
    lean = rnd.uniform(0, 2 * math.pi)
    tx, tz = x + math.cos(lean) * 1.5, z + math.sin(lean) * 1.5
    _spline_wood(wood_map, [(x, y, z), (tx, y + H, tz)], 0.65, 0.45, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=3, reach=2.0, rnd=rnd)
    for t in (0.55, 0.72, 0.88, 1.0):
        bx, by, bz = bezier_point([(x, y, z), (tx, y + H, tz)], t)
        _cloud_cluster(leaf_map, wood_map, bx + rnd.uniform(-1, 1), by, bz + rnd.uniform(-1, 1),
                       2.6 * scale, 2.0 * scale, 2.6 * scale, leaf_pick, subtract=0.25, seed=seed + int(t * 100))
    return wood_map, leaf_map, None, None


def _build_spruce(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'spruce_wood'
    leaf_pick = mix([('spruce_leaves', 82), ('azalea_leaves', 18)], seed=seed)
    wood_map, leaf_map = {}, {}
    H = max(12, int(round(rnd.randint(15, 20) * scale)))
    _spline_wood(wood_map, [(x, y, z), (x, y + H, z)], 0.9, 0.4, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=4, reach=2.4, rnd=rnd)
    tiers = 5
    for ti in range(tiers):
        yy = y + 4 + int((H - 4) * ti / float(tiers))
        r = max(1.8, (4.6 - 3.0 * (ti / float(tiers))) * scale)
        # Branch stubs so leaves 6-connect solidly
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for s in range(1, max(2, int(r) - 1)):
                wood_map[(x + dx * s, yy, z + dz * s)] = wood
        _cloud_cluster(leaf_map, wood_map, x, yy, z, r, 1.4, r, leaf_pick, subtract=0.18, seed=seed + ti * 23)
    leaf_map[(x, y + H + 1, z)] = 'spruce_leaves'
    leaf_map[(x, y + H + 2, z)] = 'spruce_leaves'
    return wood_map, leaf_map, None, None


def _build_azalea(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    wood = 'oak_wood'
    leaf_pick = mix([('azalea_leaves', 62), ('flowering_azalea_leaves', 38)], seed=seed)
    wood_map, leaf_map = {}, {}
    H = max(6, int(round(rnd.randint(7, 10) * scale)))
    ang = rnd.uniform(0, 2 * math.pi)
    tx, tz = x + math.cos(ang) * 2.0, z + math.sin(ang) * 2.0
    _spline_wood(wood_map, [(x, y, z), (tx, y + H, tz)], 0.85, 0.45, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=3, reach=2.2, rnd=rnd)
    _cloud_cluster(leaf_map, wood_map, tx, y + H, tz, 3.4 * scale, 2.2 * scale, 3.4 * scale,
                   leaf_pick, subtract=0.20, seed=seed + 11)
    _drape_leaves(leaf_map, wood_map, rnd, leaf_pick, max_drop=2, chance=0.22)
    return wood_map, leaf_map, None, 'moss_carpet'


def _build_neon_tree(canvas, x, y, z, rnd, scale=1.0, want_swing=False, seed=0):
    """Sci-fi bioluminescent canopy tree for futuristic / fantasy hubs."""
    wood = 'warped_hyphae'
    leaf_pick = mix([('flowering_azalea_leaves', 55), ('azalea_leaves', 45)], seed=seed)
    wood_map, leaf_map = {}, {}
    H = max(10, int(round(rnd.randint(11, 15) * scale)))
    ang0 = rnd.uniform(0, 2 * math.pi)
    tx0, tz0 = x + math.cos(ang0) * 2.2, z + math.sin(ang0) * 2.2
    _spline_wood(wood_map, [(x, y, z), (tx0, y + H, tz0)], 1.1 * scale, 0.5, wood)
    _grow_roots(canvas, wood_map, x, y, z, wood, count=4, reach=2.8 * scale, rnd=rnd)
    swing = _add_swing_limb(canvas, wood_map, x, y, z, wood, rnd) if want_swing else None

    tips = [(tx0, y + H + 1, tz0)]
    for i in range(4):
        ang = (2 * math.pi * i / 4.0) + rnd.uniform(-0.25, 0.25)
        sh = y + int(H * rnd.uniform(0.58, 0.85))
        reach = rnd.uniform(3.6, 5.2) * scale
        tx, ty, tz = x + math.cos(ang) * reach, sh + 2.2, z + math.sin(ang) * reach
        _spline_wood(wood_map, [(x, sh, z), (tx, ty, tz)], 0.65, 0.4, wood)
        tips.append((tx, ty, tz))

    for idx, (tx, ty, tz) in enumerate(tips):
        _cloud_cluster(leaf_map, wood_map, tx, ty + 1, tz,
                       3.2 * scale, 1.6 * scale, 3.2 * scale, leaf_pick, subtract=0.18, seed=seed + idx * 61)
    return wood_map, leaf_map, swing, 'moss_carpet'


SPECIES = {
    'sakura': _build_sakura,
    'giant_oak': _build_giant_oak,
    'weeping_willow': _build_weeping_willow,
    'japanese_pine': _build_japanese_pine,
    'autumn_maple': _build_autumn_maple,
    'birch_grove': _build_birch_grove,
    'spruce': _build_spruce,
    'azalea': _build_azalea,
    'neon_tree': _build_neon_tree,
}


def place_bamboo_clump(canvas, x, z, radius=2.6, stalks=9, part_name='Nature/Bamboo Grove', seed=0):
    """Plant a dense multi-height bamboo clump with podzol, moss boulders & lanterns."""
    rnd = _rng(seed, x, 0, z)
    placed = 0
    with canvas.part(part_name):
        ir = int(math.ceil(radius + 1))
        for dz in range(-ir, ir + 1):
            for dx in range(-ir, ir + 1):
                if dx * dx + dz * dz <= (radius + 0.5) ** 2:
                    px, pz = int(round(x)) + dx, int(round(z)) + dz
                    gy = canvas.ground_y(px, pz)
                    if gy >= 1 and canvas.get(px, gy + 1, pz) != 'water':
                        if rnd.random() < 0.65:
                            canvas.set(px, gy, pz, 'podzol' if rnd.random() < 0.6 else 'moss_block')

        used = set()
        for _ in range(stalks * 3):
            if len(used) >= stalks:
                break
            ang = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0.0, radius)
            bx, bz = int(round(x + math.cos(ang) * r)), int(round(z + math.sin(ang) * r))
            if (bx, bz) in used or not (1 <= bx < canvas.sx - 1 and 1 <= bz < canvas.sz - 1):
                continue
            gy = canvas.ground_y(bx, bz)
            if gy < 1 or canvas.get(bx, gy + 1, bz) != 'air':
                continue
            if canvas.get(bx, gy, bz) not in ('grass_block', 'dirt', 'coarse_dirt', 'podzol', 'moss_block', 'rooted_dirt', 'mud'):
                canvas.set(bx, gy, bz, 'podzol')
            h = rnd.randint(6, 12)
            used.add((bx, bz))
            for dy in range(1, h + 1):
                if gy + dy >= canvas.sy - 1:
                    break
                leaves = 'none'
                if dy >= h - 2:
                    leaves = 'large'
                elif dy >= h - 4:
                    leaves = 'small'
                canvas.set(bx, gy + dy, bz, 'bamboo', age='1', leaves=leaves, stage='0')
                placed += 1
    return {'stalks': len(used), 'blocks': placed, 'swing': None}


def place_tree(
    canvas,
    x,
    z,
    species='sakura',
    scale=1.0,
    with_swing_branch=False,
    hang_lanterns=2,
    part_name=None,
    seed=0,
):
    """Grow a grounded, 6-connected custom tree at `(x, z)` and return anchor metadata."""
    x, z = int(round(x)), int(round(z))
    if species == 'bamboo_clump':
        return place_bamboo_clump(canvas, x, z, radius=2.6 * scale, part_name=part_name or 'Nature/Bamboo Grove', seed=seed)

    if species not in SPECIES:
        raise KeyError('Unknown tree species %r. Available: %s' % (species, ', '.join(sorted(SPECIES))))

    gy = canvas.ground_y(x, z)
    if gy < 1 or canvas.get(x, gy + 1, z) == 'water' or canvas.get(x, gy, z) == 'water':
        return {'blocks': 0, 'swing': None, 'lanterns': []}

    # Ensure rich root soil pad at the trunk base (never on top of logs!)
    pname = part_name or f'Nature/Tree ({species} @{x},{z})'
    rnd = _rng(seed, x, gy, z)

    with canvas.part(pname):
        for dz in range(-1, 2):
            for dx in range(-1, 2):
                px, pz = x + dx, z + dz
                pgy = canvas.ground_y(px, pz)
                if pgy >= 1 and canvas.get(px, pgy + 1, pz) != 'water':
                    canvas.set(px, pgy, pz, 'rooted_dirt' if (dx == 0 and dz == 0) else 'podzol')

        builder = SPECIES[species]
        wood_map, leaf_map, swing, litter = builder(
            canvas, x, gy + 1, z, rnd, scale=scale, want_swing=with_swing_branch, seed=seed + x * 13 + z * 29
        )

        # Anchor trunk 3x3 core down to terrain in case of sloped hillside
        trunk_mat = next(iter(wood_map.values()), 'oak_wood')
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if abs(dx) + abs(dz) <= 1:
                    pgy = canvas.ground_y(x + dx, z + dz)
                    if pgy >= 1 and (x + dx, gy + 1, z + dz) in wood_map:
                        for yy in range(pgy + 1, gy + 2):
                            wood_map[(x + dx, yy, z + dz)] = trunk_mat

        # Remove leaves that collide with existing architecture BEFORE 6-connected pruning
        leaf_map = {
            p: v for p, v in leaf_map.items()
            if canvas.in_bounds(*p) and canvas.get(*p) == 'air'
        }
        wood_map, leaf_map = _prune_6connected(canvas, wood_map, leaf_map)

        # Clear any pre-existing small ground plants where trunk/roots land so plants aren't overwritten awkwardly
        for wx, wy, wz in wood_map:
            canvas.set(wx, wy, wz, wood_map[(wx, wy, wz)])
            # Make sure no soil block accidentally sits directly on top of a new root!
            above = canvas.get(wx, wy + 1, wz)
            if above in ('grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'moss_block', 'podzol') or above in FLAT_PLANTS:
                canvas.set(wx, wy + 1, wz, 'air')

        for lx, ly, lz in leaf_map:
            if canvas.get(lx, ly, lz) == 'air':
                canvas.set(lx, ly, lz, leaf_map[(lx, ly, lz)])

        # Optional hanging branch lanterns for atmosphere
        lantern_blk = canvas.theme.get('light', 'lantern')
        lantern_pts = []
        if hang_lanterns > 0:
            # Find wood blocks with clear air underneath
            branch_unders = [
                (wx, wy, wz) for (wx, wy, wz) in wood_map
                if wy >= gy + 5 and math.hypot(wx - x, wz - z) >= 2.2
                and canvas.get(wx, wy - 1, wz) == 'air' and canvas.get(wx, wy - 2, wz) == 'air'
                and (not swing or math.hypot(wx - swing['pos'][0], wz - swing['pos'][2]) >= 3.0)
            ]
            rnd.shuffle(branch_unders)
            for wx, wy, wz in branch_unders[:hang_lanterns]:
                canvas.set(wx, wy - 1, wz, 'chain')
                canvas.set(wx, wy - 2, wz, lantern_blk, hanging='true')
                lantern_pts.append((wx, wy - 2, wz))

        # Ground litter (fallen cherry petals or moss carpet) under the canopy
        if litter:
            for dz in range(-5, 6):
                for dx in range(-5, 6):
                    if dx * dx + dz * dz > 26:
                        continue
                    px, pz = x + dx, z + dz
                    if not (1 <= px < canvas.sx - 1 and 1 <= pz < canvas.sz - 1):
                        continue
                    pgy = canvas.ground_y(px, pz)
                    if pgy < 1 or canvas.get(px, pgy + 1, pz) != 'air':
                        continue
                    below = canvas.get(px, pgy, pz)
                    if below in NO_SUPPORT or is_foliage(below):
                        continue
                    if rnd.random() < 0.22:
                        if litter == 'pink_petals':
                            canvas.set(px, pgy + 1, pz, 'pink_petals',
                                       flower_amount=str(rnd.randint(1, 4)),
                                       facing=rnd.choice(('north', 'south', 'east', 'west')))
                        else:
                            canvas.set(px, pgy + 1, pz, litter)

        # Verify swing limb survived pruning!
        if swing is not None:
            sx_, sy_, sz_ = swing['pos']
            ax = swing['axis']
            c1 = (sx_ - 2, sy_, sz_) if ax == 'x' else (sx_, sy_, sz_ - 2)
            c2 = (sx_ + 2, sy_, sz_) if ax == 'x' else (sx_, sy_, sz_ + 2)
            if c1 not in wood_map or c2 not in wood_map:
                swing = None

    return {
        'species': species,
        'blocks': len(wood_map) + len(leaf_map),
        'swing': swing,
        'lanterns': lantern_pts,
    }
