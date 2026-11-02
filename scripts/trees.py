"""Five DISTINCT tree models, built for how Minecraft actually reads at distance.

Design rules (learned from the user's rejections)
-------------------------------------------------
* The server whitelist has exactly two wood types (jungle_wood, oak_wood) and
  two leaf types (jungle_leaves, oak_leaves).  Variety therefore has to come
  from SHAPE, not material - five clearly different silhouettes.
* No moss_block / moss_carpet sprinkled on trunks or branches.  That was the
  "random grass blocks on the main logs" the user called ugly.
* No single stray block ever sits off the canopy: every leaf is attached to the
  leaf mass, and every leaf mass touches a trunk.  `_prune` enforces that.
* Minecraft trees read best as simple, confident geometric volumes: a dome, an
  umbrella, stacked disc tiers, a twin-trunk crown, a tight ball.  Fancy
  ellipsoid noise looks like wreckage.
"""

import math
import random
from collections import deque

ALLOWED = frozenset("""
minecraft:jungle_wood minecraft:oak_wood
minecraft:jungle_leaves minecraft:oak_leaves
minecraft:lantern minecraft:iron_chain
minecraft:spruce_planks minecraft:spruce_slab minecraft:spruce_fence
minecraft:spruce_stairs minecraft:spruce_trapdoor
minecraft:glowstone minecraft:sea_lantern minecraft:pearlescent_froglight
minecraft:verdant_froglight
""".split())

_N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def _rng(seed, x, y, z):
    return random.Random((seed * 7919) ^ (x * 73856093) ^ (y * 83492791)
                         ^ (z * 19349663))


def _put(out, wood, p, name):
    out[p] = name
    wood.add(p)


# --------------------------------------------------------------- primitives
def _disc(out, wood, cx, cz, y, r, leaf, rnd, ragged=0):
    """One flat leaf disc, optionally with a ragged edge."""
    r2 = r * r
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d2 = dx * dx + dz * dz
            if d2 > r2:
                continue
            if ragged and d2 > (r - 1) * (r - 1) and rnd.random() < ragged:
                continue
            p = (cx + dx, y, cz + dz)
            if p not in out:
                out[p] = leaf


def _dome(out, wood, cx, cz, top_y, r, depth, leaf, rnd, ragged=0.0):
    """Solid-ish dome: circular footprint, height falls off with radius."""
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = math.hypot(dx, dz)
            if d > r:
                continue
            fall = (d / r) ** 2
            h = int(round(top_y - depth * fall))
            thick = 2 + int(round((1.0 - fall) * 2.5))
            if ragged and d > r - 1.2 and rnd.random() < ragged:
                thick -= 1
                if thick < 1:
                    continue
            for yy in range(h - thick + 1, h + 1):
                p = (cx + dx, yy, cz + dz)
                if p not in out:
                    out[p] = leaf


def _column(out, wood, cx, cz, y0, y1, wood_name, width=1):
    o = -(width // 2)
    for y in range(y0, y1 + 1):
        for dx in range(width):
            for dz in range(width):
                if width >= 3 and abs(dx - (width - 1) / 2.0) > width / 2.0 - 0.35 \
                        and abs(dz - (width - 1) / 2.0) > width / 2.0 - 0.35:
                    continue
                _put(out, wood, (cx + o + dx, y, cz + o + dz), wood_name)


def _branch(out, wood, x, y, z, ang, length, rise, wood_name, thick=False):
    ca, sa = math.cos(ang), math.sin(ang)
    px, py, pz = float(x), float(y), float(z)
    tip = (x, y, z)
    for s in range(1, length + 1):
        px += ca
        pz += sa
        py += rise
        ix, iy, iz = int(round(px)), int(round(py)), int(round(pz))
        _put(out, wood, (ix, iy, iz), wood_name)
        if thick and s < length * 0.6:
            _put(out, wood, (ix - int(round(sa)), iy, iz + int(round(ca))),
                 wood_name)
        tip = (ix, iy, iz)
    return tip


def _prune(out, wood):
    """Delete any leaf not connected to the trunk network."""
    keep = set(wood)
    q = deque(wood)
    while q:
        p = q.popleft()
        for d in _N6:
            n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            if n in out and n not in keep:
                keep.add(n)
                q.append(n)
    for p in [p for p in out if p not in keep]:
        del out[p]


# --------------------------------------------------------------- the models
def _m_giant_oak(x, y, z, rnd):
    """1. Broad spreading oak: thick flared trunk, wide low dome."""
    out, wood = {}, set()
    H = rnd.randint(13, 17)
    _column(out, wood, x, z, y, y + H, 'minecraft:oak_wood', width=3)
    # flare the base 2 blocks
    for dx in (-2, 2):
        for dz in (-2, 2):
            for yy in range(y, y + 3):
                _put(out, wood, (x + dx, yy, z + dz), 'minecraft:oak_wood')
    tips = []
    for i in range(5):
        ang = 2 * math.pi * i / 5 + rnd.uniform(-0.3, 0.3)
        tips.append(_branch(out, wood, x, y + H - rnd.randint(2, 4), z, ang,
                            rnd.randint(4, 6), rnd.uniform(0.25, 0.5),
                            'minecraft:oak_wood', thick=True))
    _dome(out, wood, x, z, y + H + 3, 9, 6.0, 'minecraft:oak_leaves', rnd, 0.25)
    for tx, ty, tz in tips:
        _dome(out, wood, tx, tz, ty + 2, 5, 4.0, 'minecraft:oak_leaves', rnd, 0.3)
    return out, wood


def _m_jungle_umbrella(x, y, z, rnd):
    """2. Tall jungle umbrella: clean straight trunk, flat wide canopy on top."""
    out, wood = {}, set()
    H = rnd.randint(18, 23)
    _column(out, wood, x, z, y, y + H, 'minecraft:jungle_wood', width=2)
    for i in range(4):
        ang = 2 * math.pi * i / 4 + rnd.uniform(-0.2, 0.2)
        _branch(out, wood, x, y + H - 1, z, ang, rnd.randint(3, 5),
                rnd.uniform(0.0, 0.2), 'minecraft:jungle_wood')
    top = y + H
    _disc(out, wood, x, z, top, 8, 'minecraft:jungle_leaves', rnd, 0.15)
    _disc(out, wood, x, z, top + 1, 6, 'minecraft:jungle_leaves', rnd, 0.2)
    _disc(out, wood, x, z, top + 2, 4, 'minecraft:jungle_leaves', rnd, 0.2)
    _disc(out, wood, x, z, top + 3, 2, 'minecraft:jungle_leaves', rnd, 0.0)
    return out, wood


def _m_tiered_pine(x, y, z, rnd):
    """3. Layered pine: stacked leaf rings, narrowing to a point. Reads instantly."""
    out, wood = {}, set()
    H = rnd.randint(16, 20)
    _column(out, wood, x, z, y, y + H, 'minecraft:oak_wood', width=1)
    tiers = rnd.randint(4, 5)
    for t in range(tiers):
        yy = y + 3 + int(round((H - 3) * (t + 1) / (tiers + 1.0)))
        r = int(round(7 - 5.0 * t / max(tiers - 1, 1)))
        r = max(r, 2)
        _disc(out, wood, x, z, yy, r, 'minecraft:oak_leaves', rnd, 0.0)
        if r > 2:
            _disc(out, wood, x, z, yy + 1, r - 2, 'minecraft:oak_leaves', rnd, 0.0)
    _disc(out, wood, x, z, y + H + 1, 1, 'minecraft:oak_leaves', rnd, 0.0)
    return out, wood


def _m_twin_trunk(x, y, z, rnd):
    """4. Twin trunk: two trunks from one root, two crowns. Very distinct."""
    out, wood = {}, set()
    H = rnd.randint(12, 15)
    sep = rnd.choice((2, 3))
    # shared root
    for dx in range(-1, sep + 2):
        for dz in (-1, 0, 1):
            _put(out, wood, (x + dx, y, z + dz), 'minecraft:jungle_wood')
    for side in (0, 1):
        cx = x + side * sep
        hh = H + rnd.randint(-2, 2)
        _column(out, wood, cx, z, y + 1, y + hh, 'minecraft:jungle_wood', width=2)
        for i in range(3):
            ang = 2 * math.pi * i / 3 + rnd.uniform(-0.4, 0.4)
            _branch(out, wood, cx, y + hh - rnd.randint(1, 3), z, ang,
                    rnd.randint(3, 4), rnd.uniform(0.2, 0.45),
                    'minecraft:jungle_wood')
        _dome(out, wood, cx, z, y + hh + 2, 6, 4.5,
              'minecraft:jungle_leaves', rnd, 0.25)
    return out, wood


def _m_round_bush(x, y, z, rnd):
    """5. Round bush tree: short trunk, tight ball crown. Small, decorative."""
    out, wood = {}, set()
    H = rnd.randint(8, 11)
    _column(out, wood, x, z, y, y + H, 'minecraft:oak_wood', width=2)
    r = rnd.randint(5, 6)
    _dome(out, wood, x, z, y + H + 2, r, 5.0, 'minecraft:oak_leaves', rnd, 0.0)
    # a second smaller ball slightly offset for character (still attached)
    ox, oz = rnd.choice(((1, 1), (-1, 1), (1, -1), (-1, -1)))
    _dome(out, wood, x + ox * 3, z + oz * 3, y + H - 1, 3, 2.5,
          'minecraft:oak_leaves', rnd, 0.0)
    return out, wood


MODELS = {
    'giant_oak': _m_giant_oak,
    'jungle_umbrella': _m_jungle_umbrella,
    'tiered_pine': _m_tiered_pine,
    'twin_trunk': _m_twin_trunk,
    'round_bush': _m_round_bush,
}

# name -> (leaf block, wood block) so the builder can report/count correctly
MODEL_MATERIAL = {
    'giant_oak': ('minecraft:oak_leaves', 'minecraft:oak_wood'),
    'jungle_umbrella': ('minecraft:jungle_leaves', 'minecraft:jungle_wood'),
    'tiered_pine': ('minecraft:oak_leaves', 'minecraft:oak_wood'),
    'twin_trunk': ('minecraft:jungle_leaves', 'minecraft:jungle_wood'),
    'round_bush': ('minecraft:oak_leaves', 'minecraft:oak_wood'),
}


def make_tree(x, y, z, model, seed=0):
    """Tree whose lowest trunk block is exactly (x, y, z)."""
    rnd = _rng(seed, x, y, z)
    out, wood = MODELS[model](x, y, z, rnd)
    _prune(out, wood)
    bad = set(out.values()) - ALLOWED
    assert not bad, 'block not on whitelist: %r' % (bad,)
    return out


# --------------------------------------------------------------- the swing
def make_swing(x, y, z, drop=8, axis='x'):
    """A real swing: two chains to the ground, plank seat, lantern underneath.

    (x,y,z) is the underside of the BRANCH the swing hangs from.  The chains run
    from just below it down to the seat, so the seat hangs `drop` blocks below
    the branch.  Every block is attached; nothing dangles in mid-air.
    """
    out = {}
    drop = max(4, int(drop))

    def cell(o, yy):
        return (x + o, yy, z) if axis == 'x' else (x, yy, z + o)

    for o in (-2, 2):
        for d in range(1, drop):
            out[cell(o, y - d)] = 'minecraft:iron_chain'
    seat_y = y - drop
    # seat: 5 planks, with a raised slab at each end as an armrest
    for o in range(-2, 3):
        out[cell(o, seat_y)] = 'minecraft:spruce_planks'
    for o in (-2, 2):
        out[cell(o, seat_y + 1)] = 'minecraft:spruce_slab'
    # hanging lantern under the middle of the seat
    out[cell(0, seat_y - 1)] = 'minecraft:iron_chain'
    out[cell(0, seat_y - 2)] = 'minecraft:lantern'
    bad = set(out.values()) - ALLOWED
    assert not bad, 'swing block not on whitelist: %r' % (bad,)
    return out
