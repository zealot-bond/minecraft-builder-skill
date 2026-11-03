"""Theme-aware architectural landmarks, bridges, camps, docks, pavilions & micro-props.

Every motif grounds its foundations down to `canvas.ground_y(x, z)` so nothing ever
floats on sloped terrain, and wraps blocks in named `canvas.part(...)` regions.
"""

import math
from .blocks import OPPOSITE, facing_toward
from .palette import mix, rand01
from .shapes import bezier_point


def _ground_column(canvas, x, top_y, z, block):
    """Fill foundation column from `ground_y(x, z)` up to `top_y` (even through water)."""
    x, z = int(round(x)), int(round(z))
    if not (0 <= x < canvas.sx and 0 <= z < canvas.sz):
        return
    # Walk down until we hit a solid non-water block
    y = int(round(top_y))
    by = y
    while by > 1 and canvas.get(x, by - 1, z) in ('air', 'water') or (by > 1 and canvas.get(x, by - 1, z).endswith(('_grass', 'fern', 'petals', 'carpet', 'lily_pad'))):
        by -= 1
    for yy in range(max(1, by), y + 1):
        canvas.set(x, yy, z, block)


# ------------------------------------------------------------ 1. Tree Swing
def place_swing(canvas, swing_anchor, part_name='Props/Tree Swing'):
    """Hang a 5-wide wooden swing with dual chains and under-seat lantern from `swing_anchor`."""
    if not swing_anchor:
        return False
    bx, limb_y, bz = swing_anchor['pos']
    axis = swing_anchor.get('axis', 'x')
    drop = max(4, int(swing_anchor.get('drop', 5)))
    wood_fam = canvas.theme['wood']
    lantern_blk = canvas.theme.get('light', 'lantern')

    def cell(o, yy):
        return (bx + o, yy, bz) if axis == 'x' else (bx, yy, bz + o)

    with canvas.part(part_name):
        # Ensure crossbar wood exists directly above both chains
        for o in (-2, -1, 0, 1, 2):
            cx_, yy, cz_ = cell(o, limb_y)
            if not canvas.get(cx_, yy, cz_).endswith(('_wood', '_log', '_hyphae', '_stem')):
                canvas.set(cx_, yy, cz_, wood_fam['wood'])

        seat_y = limb_y - drop
        for o in (-2, 2):
            for d in range(1, drop):
                canvas.set(*cell(o, limb_y - d), 'chain')

        for o in (-2, -1, 0, 1, 2):
            canvas.set(*cell(o, seat_y), wood_fam['slab'], type='top')
        for o in (-2, 2):
            canvas.set(*cell(o, seat_y + 1), wood_fam['trapdoor'], half='bottom', open='false')

        # Cozy lantern tucked 1 block below center if clearance allows
        ux, uy, uz = cell(0, seat_y - 1)
        if uy >= 2 and canvas.get(ux, uy, uz) == 'air' and canvas.get(ux, uy - 1, uz) != 'air':
            canvas.set(ux, uy, uz, lantern_blk, hanging='true')
        elif uy >= 3 and canvas.get(ux, uy, uz) == 'air' and canvas.get(ux, uy - 1, uz) == 'air':
            canvas.set(ux, uy, uz, 'chain')
            canvas.set(ux, uy - 1, uz, lantern_blk, hanging='true')
    return True


# ------------------------------------------------------------ 2. Arched / Drum Bridge
def place_bridge(
    canvas,
    p_start,
    p_end,
    arch_height=3.2,
    half_width=1,
    part_name='Architecture/Pond Bridge',
):
    """Build an arched timber/lacquer or stone/neon bridge between `(x0, z0)` and `(x1, z1)`
    with solid submerged piers, smooth slab steps, railings, and post lanterns.
    """
    x0, z0 = p_start[0], p_start[-1]
    x1, z1 = p_end[0], p_end[-1]
    y0 = p_start[1] if len(p_start) == 3 else max(4, canvas.ground_y(x0, z0))
    y1 = p_end[1] if len(p_end) == 3 else max(4, canvas.ground_y(x1, z1))

    theme = canvas.theme
    deck_fam = theme['bridge_deck']
    rail_fam = theme['bridge_rail']
    stone_fam = theme['dark_stone']
    lantern_blk = theme.get('light', 'lantern')

    dx_tot, dz_tot = float(x1 - x0), float(z1 - z0)
    span = max(1.0, math.hypot(dx_tot, dz_tot))
    # Unit forward & perpendicular vectors
    ux, uz = dx_tot / span, dz_tot / span
    px, pz = -uz, ux  # perpendicular horizontal

    steps = max(16, int(math.ceil(span * 3.0)))
    deck_cols = {}
    rail_cols = {}

    for i in range(steps + 1):
        t = i / float(steps)
        cx_ = x0 + dx_tot * t
        cz_ = z0 + dz_tot * t
        base_h = y0 + (y1 - y0) * t
        # Parabolic / sine arch peaking at t=0.5
        arch = math.sin(math.pi * t) * arch_height
        exact_y = base_h + arch + 0.5

        for w in range(-half_width, half_width + 1):
            bx = int(round(cx_ + px * w))
            bz = int(round(cz_ + pz * w))
            if (bx, bz) not in deck_cols or exact_y > deck_cols[(bx, bz)]:
                deck_cols[(bx, bz)] = exact_y

        for w in (-half_width - 1, half_width + 1):
            rx = int(round(cx_ + px * w))
            rz = int(round(cz_ + pz * w))
            if (rx, rz) not in rail_cols or exact_y > rail_cols[(rx, rz)][0]:
                rail_cols[(rx, rz)] = (exact_y, t)

    with canvas.part(part_name):
        # Clear foliage/lilypads in bridge corridor and place smooth slab deck
        for (bx, bz), ey in deck_cols.items():
            iy = int(math.floor(ey))
            frac = ey - iy
            # Clear headroom above deck
            for hy in range(iy, min(canvas.sy, iy + 5)):
                canvas.set(bx, hy, bz, 'air')
            if frac < 0.5:
                canvas.set(bx, iy, bz, deck_fam['slab'], type='bottom')
                # Solid under-arch beam so there are never diagonal gaps!
                canvas.set(bx, iy - 1, bz, deck_fam['slab'], type='top')
            else:
                canvas.set(bx, iy, bz, deck_fam['planks'] if 'planks' in deck_fam else deck_fam['block'])
                canvas.set(bx, iy - 1, bz, deck_fam['slab'], type='top')

        # Side arch fascia + railings
        rail_fence = rail_fam.get('fence', rail_fam.get('wall', 'dark_oak_fence'))
        rail_post = rail_fam.get('wood', rail_fam.get('log', stone_fam['block']))
        for (rx, rz), (ey, t) in rail_cols.items():
            if (rx, rz) in deck_cols:
                continue
            iy = int(math.floor(ey))
            for hy in range(iy, min(canvas.sy, iy + 4)):
                canvas.set(rx, hy, rz, 'air')
            # Structural stringer beam
            canvas.set(rx, iy, rz, rail_fam.get('slab', deck_fam['slab']), type='top')
            canvas.set(rx, iy + 1, rz, rail_fence)

        # Four end-posts + two mid-span lantern posts anchored solidly down into bed
        for t_post, anchor_ground in ((0.03, True), (0.50, True), (0.97, True)):
            cx_ = x0 + dx_tot * t_post
            cz_ = z0 + dz_tot * t_post
            base_h = y0 + (y1 - y0) * t_post + math.sin(math.pi * t_post) * arch_height + 0.5
            iy = int(math.floor(base_h))
            for side in (-half_width - 1, half_width + 1):
                px_ = int(round(cx_ + px * side))
                pz_ = int(round(cz_ + pz * side))
                if anchor_ground:
                    _ground_column(canvas, px_, iy, pz_, stone_fam['block'] if t_post == 0.50 else rail_post)
                canvas.set(px_, iy + 1, pz_, rail_post)
                canvas.set(px_, iy + 2, pz_, rail_fence)
                canvas.set(px_, iy + 3, pz_, lantern_blk, hanging='false')

        # Entry ramp steps at both ends so players walk smoothly onto the bridge
        for end_x, end_z, dir_sign in ((x0, z0, -1), (x1, z1, 1)):
            ex = int(round(end_x + ux * dir_sign))
            ez = int(round(end_z + uz * dir_sign))
            gy = canvas.ground_y(ex, ez)
            if gy >= 2:
                for w in range(-half_width, half_width + 1):
                    sx_ = int(round(ex + px * w))
                    sz_ = int(round(ez + pz * w))
                    sgy = canvas.ground_y(sx_, sz_)
                    if sgy >= 2 and canvas.get(sx_, sgy + 1, sz_) == 'air':
                        canvas.set(sx_, sgy + 1, sz_, deck_fam['slab'], type='bottom')

    canvas.register_landmark('Bridge', (x0 + x1) / 2, max(y0, y1) + arch_height + 1, (z0 + z1) / 2)
    return {'deck_cols': set(deck_cols.keys()) | set(rail_cols.keys())}


# ------------------------------------------------------------ 3. Campfire Camp
def place_campfire_camp(
    canvas,
    cx,
    cz,
    radius=5.2,
    tents=2,
    part_name='Zones/Campfire Camp',
    seed=505,
):
    """Build a full adventurer campsite: stone hearth, roaring campfire, cooking spit,
    log benches, A-frame striped tents with gear inside, firewood stack, barrels & lanterns.
    """
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return {}
    theme = canvas.theme
    wood_fam = theme['accent_wood']
    log_blk = wood_fam.get('stripped_log', wood_fam.get('log', 'stripped_spruce_log'))
    tent_palettes = theme.get('tent_colors', [('pink_wool', 'white_wool'), ('white_wool', 'pink_wool')])
    lantern_blk = theme.get('light', 'lantern')

    occupied = set()
    with canvas.part(part_name):
        # 1. Textured camp clearing pad (coarse dirt, gravel, cobble, path)
        pad_mix = mix([('coarse_dirt', 4), ('dirt_path', 3), ('gravel', 2), ('cobblestone', 1), ('podzol', 2)], seed=seed)
        ir = int(math.ceil(radius))
        for dz in range(-ir, ir + 1):
            for dx in range(-ir, ir + 1):
                if dx * dx + dz * dz <= radius * radius:
                    px, pz = cx + dx, cz + dz
                    pgy = canvas.ground_y(px, pz)
                    if pgy >= 2 and canvas.get(px, pgy + 1, pz) != 'water':
                        if rand01(px, pgy, pz, seed + 3) < 0.78:
                            canvas.set(px, pgy, pz, pad_mix(px, pgy, pz))
                        occupied.add((px, pz))

        # 2. Central campfire hearth + cooking spit frame
        _ground_column(canvas, cx, gy, cz, 'cobblestone')
        canvas.set(cx, gy, cz, 'magma_block' if theme['id'] == 'futuristic' else 'cobblestone')
        canvas.set(cx, gy + 1, cz, 'soul_campfire' if theme.get('light') == 'soul_lantern' else 'campfire',
                   lit='true', signal_fire='false', facing='north')
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            hx, hz = cx + dx, cz + dz
            hgy = canvas.ground_y(hx, hz)
            if hgy == gy and canvas.get(hx, gy + 1, hz) == 'air':
                canvas.set(hx, gy, hz, 'mossy_cobblestone' if (dx + dz) % 2 == 0 else 'cobblestone')
                if dx != 0 and dz == 0:
                    # Cooking spit posts on East & West of fire!
                    canvas.set(hx, gy + 1, hz, wood_fam['fence'])
                    canvas.set(hx, gy + 2, hz, wood_fam['fence'])
        # Crossbar over campfire at gy + 3
        for dx in (-1, 0, 1):
            canvas.set(cx + dx, gy + 3, cz, wood_fam['slab'], type='bottom')
        canvas.set(cx, gy + 2, cz, 'chain')

        # 3. Two curved log benches (North & South of the fire, 2-3 blocks away)
        for bz_off, stair_face in ((-3, 'south'), (3, 'north')):
            bz = cz + bz_off
            for dx in (-1, 0, 1):
                bx = cx + dx
                bgy = canvas.ground_y(bx, bz)
                if bgy >= 2 and abs(bgy - gy) <= 1 and canvas.get(bx, bgy + 1, bz) == 'air':
                    _ground_column(canvas, bx, bgy, bz, 'coarse_dirt')
                    canvas.set(bx, bgy + 1, bz, log_blk, axis='x')
            # Trapdoor / slab armrests at bench ends
            for end_dx in (-2, 2):
                ex = cx + end_dx
                egy = canvas.ground_y(ex, bz)
                if egy == gy and canvas.get(ex, egy + 1, bz) == 'air':
                    canvas.set(ex, egy + 1, bz, wood_fam['slab'], type='bottom')

        # 4. A-frame adventurer tents!
        tent_configs = [
            (cx - 5, cz - 1, 'z', tent_palettes[0]),
            (cx + 5, cz + 1, 'z', tent_palettes[min(1, len(tent_palettes) - 1)]),
        ][:max(0, int(tents))]

        for tx, tz, axis, (c_main, c_stripe) in tent_configs:
            if not (4 <= tx < canvas.sx - 4 and 4 <= tz < canvas.sz - 4):
                continue
            tgy = canvas.ground_y(tx, tz)
            if tgy < 2 or abs(tgy - gy) > 2:
                continue
            # Tent is 5 wide (across tent opening) x 4 deep (along ridgepole)
            for l_step in range(-2, 2):  # 4 blocks deep along ridge
                stripe = c_main if (l_step % 2 == 0) else c_stripe
                for w_step in (-2, -1, 0, 1, 2):
                    px = tx + (w_step if axis == 'x' else l_step)
                    pz = tz + (l_step if axis == 'x' else w_step)
                    occupied.add((px, pz))
                    _ground_column(canvas, px, tgy, pz, 'coarse_dirt')
                    # Clear space first
                    for cl_y in range(tgy + 1, tgy + 5):
                        canvas.set(px, cl_y, pz, 'air')
                    # Floor carpet inside tent
                    if abs(w_step) <= 1:
                        canvas.set(px, tgy, pz, wood_fam['planks'])
                    # Sloping A-frame canvas walls
                    if abs(w_step) == 2:
                        canvas.set(px, tgy + 1, pz, stripe)
                    elif abs(w_step) == 1:
                        canvas.set(px, tgy + 2, pz, stripe)
                    elif w_step == 0:
                        canvas.set(px, tgy + 3, pz, stripe)
                        canvas.set(px, tgy + 2, pz, wood_fam['fence'] if l_step in (-2, 1) else 'air')
                # Ridgepole extending 1 block at front & back
            # Ridgepole timber cap + hanging lantern at front opening
            front_x = tx + (0 if axis == 'x' else 2)
            front_z = tz + (2 if axis == 'x' else 0)
            if canvas.in_bounds(front_x, tgy + 3, front_z):
                canvas.set(front_x, tgy + 3, front_z, wood_fam['slab'], type='bottom')
                if canvas.get(front_x, tgy + 2, front_z) == 'air':
                    canvas.set(front_x, tgy + 2, front_z, lantern_blk, hanging='true')
            # Gear tucked inside tent back
            canvas.set(tx, tgy + 1, tz, 'chest', facing='east' if tx < cx else 'west')
            bx_in = tx + (1 if axis == 'x' else 0)
            bz_in = tz + (0 if axis == 'x' else 1)
            canvas.set(bx_in, tgy + 1, bz_in, 'barrel', facing='up')

        # 5. Supply barrels, crafting station & camp lantern post
        sup_x, sup_z = cx + 3, cz - 3
        sgy = canvas.ground_y(sup_x, sup_z)
        if sgy >= 2 and canvas.get(sup_x, sgy + 1, sup_z) == 'air':
            canvas.set(sup_x, sgy + 1, sup_z, 'barrel', facing='up')
            if canvas.get(sup_x + 1, canvas.ground_y(sup_x + 1, sup_z) + 1, sup_z) == 'air':
                canvas.set(sup_x + 1, canvas.ground_y(sup_x + 1, sup_z) + 1, sup_z, 'crafting_table')
            canvas.set(sup_x, sgy + 2, sup_z, lantern_blk, hanging='false')

    canvas.register_landmark('Campfire Camp', cx, gy + 2, cz)
    return {'occupied': occupied}


# ------------------------------------------------------------ 4. Multi-Tier Pagoda / Shrine
def place_pagoda(
    canvas,
    cx,
    cz,
    tiers=3,
    base_half=4,
    part_name='Landmarks/Pagoda Shrine',
):
    """Build a dramatic multi-tier pagoda with stepped stone plinth, recessed plaster
    walls, dark timber pillars, upturned eaves, hanging corner lanterns, and tall finial spire.
    """
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return {}
    theme = canvas.theme
    stone_fam = theme['stone']
    pillar_blk = theme['accent_wood'].get('wood', theme['accent_wood'].get('log', 'dark_oak_wood'))
    wall_mix = mix(theme.get('light_wall', ['white_concrete', 'calcite']), seed=cx * 17 + cz)
    roof_fam = theme['roof']
    eave_fam = theme['roof_accent']
    lantern_blk = theme.get('light', 'lantern')
    glow_blk = theme.get('glow_block', 'pearlescent_froglight')
    pane_blk = theme.get('glass_pane', 'pink_stained_glass_pane')

    occupied = set()
    with canvas.part(part_name):
        # 1. Grounded stone plinth (2 blocks tall) with stairs on all 4 cardinal entries
        p_half = base_half + 1
        plinth_top = gy + 1
        for dz in range(-p_half - 1, p_half + 2):
            for dx in range(-p_half - 1, p_half + 2):
                px, pz = cx + dx, cz + dz
                occupied.add((px, pz))
                if abs(dx) <= p_half and abs(dz) <= p_half:
                    _ground_column(canvas, px, plinth_top, pz, stone_fam['block'])
                    # Clear air above plinth
                    for cy_ in range(plinth_top + 1, min(canvas.sy, plinth_top + 24)):
                        canvas.set(px, cy_, pz, 'air')
                elif (abs(dx) == p_half + 1 and abs(dz) <= 1) or (abs(dz) == p_half + 1 and abs(dx) <= 1):
                    # Cardinal stair steps leading up onto plinth
                    _ground_column(canvas, px, plinth_top - 1, pz, stone_fam['block'])
                    face = facing_toward(-dx, -dz)
                    canvas.set(px, plinth_top, pz, stone_fam['stairs'], facing=face, half='bottom')

        cur_y = plinth_top + 1
        for t in range(tiers):
            h_wall = 4 if t == 0 else 3
            w_half = max(2, base_half - t)

            # Floor of tier
            for dz in range(-w_half, w_half + 1):
                for dx in range(-w_half, w_half + 1):
                    canvas.set(cx + dx, cur_y - 1, cz + dz, theme['wood']['planks'])

            # Recessed walls + proud corner pillars (3D Depth Rule!)
            for dy in range(h_wall):
                yy = cur_y + dy
                for dz in range(-w_half, w_half + 1):
                    for dx in range(-w_half, w_half + 1):
                        ax, az = abs(dx), abs(dz)
                        if ax == w_half and az == w_half:
                            # Corner timber column stands proud
                            canvas.set(cx + dx, yy, cz + dz, pillar_blk)
                        elif ax == w_half or az == w_half:
                            # Outer ring: timber top beam at dy == h_wall - 1, doorways on tier 0
                            if dy == h_wall - 1:
                                canvas.set(cx + dx, yy, cz + dz, pillar_blk)
                            elif t == 0 and (ax == 0 or az == 0) and dy <= 2:
                                # Open archway entrance on ground tier!
                                if dy == 2:
                                    canvas.set(cx + dx, yy, cz + dz, theme['wood']['trapdoor'], half='top')
                            else:
                                # Leave outer ring recessed by placing walls 1 block INWARD if w_half >= 3,
                                # or textured framing here on compact top tiers
                                if w_half >= 3:
                                    if (ax == 1 or az == 1) and dy == 0:
                                        canvas.set(cx + dx, yy, cz + dz, stone_fam['slab'], type='bottom')
                                else:
                                    blk = pane_blk if (dy == 1 and (ax == 0 or az == 0)) else wall_mix(cx + dx, yy, cz + dz)
                                    canvas.set(cx + dx, yy, cz + dz, blk)
                        elif w_half >= 3 and (ax == w_half - 1 or az == w_half - 1):
                            # Recessed inner wall plane!
                            if t == 0 and (ax == 0 or az == 0) and dy <= 1:
                                continue  # open doorway into luminous shrine core
                            if dy == 1 and (ax == 0 or az == 0):
                                canvas.set(cx + dx, yy, cz + dz, pane_blk)
                            else:
                                canvas.set(cx + dx, yy, cz + dz, wall_mix(cx + dx, yy, cz + dz))

            # Glowing shrine heart inside each tier
            canvas.set(cx, cur_y, cz, glow_blk)
            if t == 0:
                canvas.set(cx, cur_y + 1, cz, lantern_blk, hanging='false')

            # Sweeping overhanging roof skirt + upturned dragon-tail corners!
            roof_y = cur_y + h_wall
            r_half = w_half + 2
            for dz in range(-r_half, r_half + 1):
                for dx in range(-r_half, r_half + 1):
                    ax, az = abs(dx), abs(dz)
                    px, pz = cx + dx, cz + dz
                    if ax == r_half and az == r_half:
                        # Upturned corner tip!
                        canvas.set(px, roof_y, pz, eave_fam['slab'], type='top')
                        canvas.set(px, roof_y + 1, pz, eave_fam['slab'], type='bottom')
                        # Hanging lantern under the 4 corners of lower tiers!
                        if t <= 1 and canvas.get(px, roof_y - 1, pz) == 'air':
                            canvas.set(px, roof_y - 1, pz, 'chain')
                            if canvas.get(px, roof_y - 2, pz) == 'air':
                                canvas.set(px, roof_y - 2, pz, lantern_blk, hanging='true')
                    elif ax == r_half or az == r_half:
                        # Outer eave rim in accent trim slab
                        canvas.set(px, roof_y, pz, eave_fam['slab'], type='bottom')
                    elif ax == r_half - 1 or az == r_half - 1:
                        # Sloping roof body
                        face = facing_toward(-dx if ax >= az else 0, -dz if az > ax else 0)
                        canvas.set(px, roof_y, pz, roof_fam['block'])
                        canvas.set(px, roof_y + 1, pz, roof_fam['stairs'], facing=face, half='bottom')
                    else:
                        canvas.set(px, roof_y, pz, roof_fam['block'])
                        canvas.set(px, roof_y + 1, pz, roof_fam['block'])

            cur_y = roof_y + 2

        # Crown roof peak & tall finial spire (sorin)
        canvas.set(cx, cur_y, cz, roof_fam['block'])
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            canvas.set(cx + dx, cur_y, cz + dz, roof_fam['stairs'], facing=facing_toward(-dx, -dz), half='bottom')
        canvas.set(cx, cur_y + 1, cz, stone_fam['wall'])
        canvas.set(cx, cur_y + 2, cz, eave_fam.get('fence', stone_fam['wall']))
        canvas.set(cx, cur_y + 3, cz, 'chain')
        canvas.set(cx, cur_y + 4, cz, 'end_rod', facing='up')
        peak_y = cur_y + 4

    canvas.register_landmark('Pagoda Shrine', cx, gy + 5, cz)
    return {'peak_y': peak_y, 'occupied': occupied}


# ------------------------------------------------------------ 5. Torii Gate
def place_torii_gate(canvas, cx, cz, axis='x', half_span=3, height=7, part_name='Landmarks/Torii Gate'):
    """Build a detailed vermilion/themed Torii gate with stone pedestals, twin columns,
    tie-beam (`nuki`), central tablet, upturned double lintel (`kasagi`), and lanterns.
    """
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return {}
    theme = canvas.theme
    red_fam = theme['roof_accent']
    col_blk = red_fam.get(
        'stripped_wood',
        red_fam.get('wood', red_fam.get('block', 'stripped_mangrove_wood')),
    )
    col_has_axis = col_blk.endswith(('log', 'wood', 'stem', 'hyphae', 'pillar'))
    cap_fam = theme['roof']
    stone_blk = theme['dark_stone']['block']
    stone_wall = theme['dark_stone']['wall']
    lantern_blk = theme.get('light', 'lantern')

    def pt(offset, y):
        return (cx + offset, y, cz) if axis == 'x' else (cx, y, cz + offset)

    with canvas.part(part_name):
        # Twin pillars grounded into terrain
        for off in (-half_span, half_span):
            px, _, pz = pt(off, gy)
            _ground_column(canvas, px, gy + 1, pz, stone_blk)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if canvas.ground_y(px + dx, pz + dz) == gy:
                    canvas.set(px + dx, gy + 1, pz + dz, theme['dark_stone']['slab'], type='bottom')
            for dy in range(2, height + 1):
                canvas.set(*pt(off, gy + dy), col_blk)

        # Lower tie-beam (nuki) extending 1 block past pillars
        nuki_y = gy + height - 2
        beam_kw = {'axis': 'x' if axis == 'x' else 'z'} if col_has_axis else {}
        for off in range(-half_span - 1, half_span + 2):
            canvas.set(*pt(off, nuki_y), col_blk, **beam_kw)

        # Central tablet (gakuzuka) between nuki and kasagi
        canvas.set(*pt(0, nuki_y + 1), red_fam.get('fence', red_fam.get('wall', stone_wall)))
        # Hanging lantern under each side of the nuki!
        for off in (-half_span + 1, half_span - 1):
            lx, ly, lz = pt(off, nuki_y - 1)
            if canvas.get(lx, ly, lz) == 'air':
                canvas.set(lx, ly, lz, lantern_blk, hanging='true')

        # Sweeping top lintel (shimaki + dark kasagi cap with upturned tips!)
        top_y = gy + height + 1
        for off in range(-half_span - 2, half_span + 3):
            if abs(off) == half_span + 2:
                canvas.set(*pt(off, top_y), red_fam['slab'], type='top')
                canvas.set(*pt(off, top_y + 1), cap_fam['slab'], type='bottom')
                canvas.set(*pt(off + (1 if off > 0 else -1), top_y + 1), cap_fam['slab'], type='top')
            else:
                canvas.set(*pt(off, top_y), col_blk, **beam_kw)
                canvas.set(*pt(off, top_y + 1), cap_fam['slab'], type='bottom')

    canvas.register_landmark('Torii Gate', cx, gy + 3, cz)
    return {'top_y': top_y + 1}


# ------------------------------------------------------------ 6. Pavilion / Holo-Gazebo
def place_gazebo(canvas, cx, cz, radius=3, part_name='Architecture/Pavilion'):
    """Build an open-air pavilion / futuristic holo-rotunda with corner pillars,
    fenced balustrades, layered dome/pagoda roof, and central chandelier.
    """
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return {}
    theme = canvas.theme
    stone_fam = theme['stone']
    wood_fam = theme['wood']
    roof_fam = theme['roof']
    accent_fam = theme['roof_accent']
    lantern_blk = theme.get('light', 'lantern')
    glow_blk = theme.get('glow_block', 'sea_lantern')

    r = int(round(radius))
    floor_y = gy + 1
    with canvas.part(part_name):
        # Rounded square floor plinth + cardinal steps
        for dz in range(-r - 1, r + 2):
            for dx in range(-r - 1, r + 2):
                ax, az = abs(dx), abs(dz)
                px, pz = cx + dx, cz + dz
                if ax <= r and az <= r and not (ax == r and az == r and r >= 4):
                    _ground_column(canvas, px, floor_y, pz, stone_fam['block'])
                    for cy_ in range(floor_y + 1, min(canvas.sy, floor_y + 11)):
                        canvas.set(px, cy_, pz, 'air')
                    if ax < r and az < r:
                        canvas.set(px, floor_y, pz, wood_fam.get('planks', stone_fam['block']))
                elif (ax == r + 1 and az <= 1) or (az == r + 1 and ax <= 1):
                    _ground_column(canvas, px, floor_y - 1, pz, stone_fam['block'])
                    canvas.set(px, floor_y, pz, stone_fam['stairs'], facing=facing_toward(-dx, -dz), half='bottom')

        # Central inlaid glow block
        canvas.set(cx, floor_y, cz, glow_blk)

        # Corner columns + side balustrades (open cardinal entries)
        col_blk = theme['accent_wood'].get('wood', stone_fam['block'])
        if theme['id'] == 'futuristic':
            col_blk = theme['dark_stone']['block']
        posts = [(-r + 1, -r + 1), (r - 1, -r + 1), (-r + 1, r - 1), (r - 1, r - 1)] if r >= 4 else [(-r, -r), (r, -r), (-r, r), (r, r)]
        for dx, dz in posts:
            for dy in range(1, 5):
                canvas.set(cx + dx, floor_y + dy, cz + dz, col_blk)

        # Balustrades on non-entry rim blocks
        rail = wood_fam.get('fence', stone_fam['wall'])
        for dz in range(-r, r + 1):
            for dx in range(-r, r + 1):
                ax, az = abs(dx), abs(dz)
                if (ax == r or az == r) and not (ax == r and az == r and r >= 4):
                    if ax > 1 and az > 1 or (ax == r and az == 2) or (az == r and ax == 2):
                        if canvas.get(cx + dx, floor_y + 1, cz + dz) == 'air':
                            canvas.set(cx + dx, floor_y + 1, cz + dz, rail)

        # Tiered roof canopy
        ry = floor_y + 5
        for dz in range(-r - 1, r + 2):
            for dx in range(-r - 1, r + 2):
                ax, az = abs(dx), abs(dz)
                d = math.hypot(dx, dz)
                px, pz = cx + dx, cz + dz
                if d <= r + 1.35:
                    if d >= r + 0.35:
                        canvas.set(px, ry, pz, accent_fam['slab'], type='bottom')
                    elif d >= r - 1.1:
                        canvas.set(px, ry, pz, roof_fam['block'])
                        canvas.set(px, ry + 1, pz, roof_fam['slab'], type='bottom')
                    else:
                        canvas.set(px, ry + 1, pz, roof_fam['block'])
                        if d <= 1.5:
                            canvas.set(px, ry + 2, pz, accent_fam['slab'], type='bottom')
        # Finial + hanging chandelier
        canvas.set(cx, ry + 2, cz, roof_fam['block'])
        canvas.set(cx, ry + 3, cz, stone_fam['wall'])
        canvas.set(cx, ry + 4, cz, 'end_rod' if theme['id'] == 'futuristic' else lantern_blk,
                   **({'facing': 'up'} if theme['id'] == 'futuristic' else {'hanging': 'false'}))
        canvas.set(cx, ry, cz, 'chain')
        canvas.set(cx, ry - 1, cz, lantern_blk, hanging='true')

    canvas.register_landmark('Pavilion', cx, floor_y + 2, cz)
    return {'roof_y': ry + 4}


# ------------------------------------------------------------ 7. Neon Holo-Spire (Futuristic Hero)
def place_holo_spire(canvas, cx, cz, radius=5, height=19, part_name='Landmarks/Holo Energy Spire'):
    """Hero centerpiece for futuristic/solarpunk builds: sunken glowing prismarine/water
    ring basin, 4 sweeping quartz buttress fins, suspended cyan glass holo-rings, and beacon core.
    """
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 3:
        return {}
    theme = canvas.theme
    q_fam = theme['stone']       # smooth_quartz
    d_fam = theme['dark_stone']  # deepslate_tiles
    glass_blk = theme.get('glass', 'cyan_stained_glass')
    glow_blk = theme.get('glow_block', 'sea_lantern')

    with canvas.part(part_name):
        # 1. Grounded circular stepped plaza & watertight glowing moat!
        ir = radius + 2
        for dz in range(-ir, ir + 1):
            for dx in range(-ir, ir + 1):
                d = math.hypot(dx, dz)
                px, pz = cx + dx, cz + dz
                if d <= ir:
                    _ground_column(canvas, px, gy, pz, d_fam['block'])
                    for cy_ in range(gy + 1, min(canvas.sy, gy + height + 3)):
                        canvas.set(px, cy_, pz, 'air')
                    if d <= 2.2:
                        canvas.set(px, gy, pz, q_fam['block'])
                        canvas.set(px, gy + 1, pz, d_fam['block'])
                    elif d <= radius - 0.6:
                        # Watertight sunken glowing ring pool at gy!
                        canvas.set(px, gy - 1, pz, glow_blk if (dx + dz) % 2 == 0 else 'dark_prismarine')
                        canvas.set(px, gy, pz, 'water', level='0')
                    else:
                        # Solid quartz retaining rim around water at gy (watertight!)
                        canvas.set(px, gy, pz, q_fam['block'])
                        if d <= radius + 0.6 and abs(dx) > 1 and abs(dz) > 1:
                            canvas.set(px, gy + 1, pz, q_fam['slab'], type='bottom')

        # Seal any diagonal water adjacency just in case
        for dz in range(-ir, ir + 1):
            for dx in range(-ir, ir + 1):
                px, pz = cx + dx, cz + dz
                if canvas.get(px, gy, pz) == 'water':
                    for ndx, ndz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if canvas.get(px + ndx, gy, pz + ndz) not in ('water', q_fam['block'], d_fam['block']):
                            canvas.set(px + ndx, gy, pz + ndz, q_fam['block'])

        # 2. Central luminous energy column + 4 sweeping buttress fins
        for dy in range(1, height + 1):
            yy = gy + dy
            if dy % 3 == 0:
                canvas.set(cx, yy, cz, glow_blk)
            else:
                canvas.set(cx, yy, cz, glass_blk)

        for fdx, fdz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in range(1, height - 2):
                t = dy / float(height - 2)
                reach = int(round(1 + (1.0 - t) ** 1.4 * (radius - 1)))
                for r_step in range(1, reach + 1):
                    bx, bz = cx + fdx * r_step, cz + fdz * r_step
                    if r_step == reach:
                        canvas.set(bx, gy + dy, bz, q_fam['block'])
                    elif r_step == 1 and dy % 2 == 1:
                        canvas.set(bx, gy + dy, bz, d_fam['wall'])

        # 3. Two orbiting holo-rings connected directly through the 4 buttress fins!
        for ring_dy, ring_r in ((int(height * 0.42), radius - 1), (int(height * 0.72), max(3, radius - 2))):
            ry = gy + ring_dy
            for dz in range(-ring_r - 1, ring_r + 2):
                for dx in range(-ring_r - 1, ring_r + 2):
                    d = math.hypot(dx, dz)
                    if ring_r - 0.65 <= d <= ring_r + 0.55:
                        blk = glow_blk if (abs(dx) <= 1 or abs(dz) <= 1) else glass_blk
                        canvas.set(cx + dx, ry, cz + dz, blk)

        # Spire tip
        canvas.set(cx, gy + height + 1, cz, q_fam['slab'], type='bottom')
        canvas.set(cx, gy + height + 2, cz, 'end_rod', facing='up')
        canvas.set(cx, gy + height + 3, cz, 'end_rod', facing='up')

    canvas.register_landmark('Holo Energy Spire', cx, gy + 5, cz)
    return {'peak_y': gy + height + 3}


# ------------------------------------------------------------ 8. Pond Dock / Pier
def place_dock(canvas, start_xz, dir_dx, dir_dz, length=6, half_width=1, water_y=8, part_name='Architecture/Pond Dock'):
    """Build a wooden pier jutting out over water on submerged log pilings, with barrels & lantern."""
    sx_, sz_ = int(round(start_xz[0])), int(round(start_xz[1]))
    if abs(dir_dx) >= abs(dir_dz):
        fdx, fdz = (1 if dir_dx >= 0 else -1), 0
        pdx, pdz = 0, 1
    else:
        fdx, fdz = 0, (1 if dir_dz >= 0 else -1)
        pdx, pdz = 1, 0

    wood_fam = canvas.theme['accent_wood']
    deck_y = water_y + 1
    lantern_blk = canvas.theme.get('light', 'lantern')

    with canvas.part(part_name):
        for s in range(length):
            for w in range(-half_width, half_width + 1):
                px = sx_ + fdx * s + pdx * w
                pz = sz_ + fdz * s + pdz * w
                if not (1 <= px < canvas.sx - 1 and 1 <= pz < canvas.sz - 1):
                    continue
                canvas.set(px, deck_y + 1, pz, 'air')
                canvas.set(px, deck_y, pz, wood_fam['slab'], type='bottom')
                # Pilings at start, middle, and tip corners grounded all the way down through water!
                if abs(w) == half_width and (s in (0, length - 1) or s == length // 2):
                    _ground_column(canvas, px, deck_y, pz, wood_fam.get('wood', 'spruce_wood'))
                    canvas.set(px, deck_y + 1, pz, wood_fam['fence'])
                    if s == length - 1 and w == half_width:
                        canvas.set(px, deck_y + 2, pz, lantern_blk, hanging='false')
        # Barrel & fishing crate at tip
        tx = sx_ + fdx * (length - 1) - pdx * half_width
        tz = sz_ + fdz * (length - 1) - pdz * half_width
        if canvas.in_bounds(tx, deck_y + 1, tz):
            canvas.set(tx, deck_y, tz, wood_fam['planks'])
            canvas.set(tx, deck_y + 1, tz, 'barrel', facing='up')


# ------------------------------------------------------------ 9. Market Stall, Lamps, Benches, Zen Garden, Spawn Pad
def place_market_stall(canvas, cx, cz, facing='south', color_pair=None, part_name='Props/Market Stall'):
    """Build a cozy market stall with timber counter, striped wool canopy, barrels & lantern."""
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return
    theme = canvas.theme
    wood_fam = theme['wood']
    c1, c2 = color_pair or theme.get('tent_colors', [('pink_wool', 'white_wool')])[0]
    lantern_blk = theme.get('light', 'lantern')
    along_x = facing in ('north', 'south')
    front_sign = 1 if facing in ('south', 'east') else -1

    def pt(u, v, dy):
        # u across width (-2..2), v front/back (-1..1)
        if along_x:
            return cx + u, gy + dy, cz + v * front_sign
        return cx + v * front_sign, gy + dy, cz + u

    with canvas.part(part_name):
        for v in (-1, 0, 1):
            for u in range(-2, 3):
                px, _, pz = pt(u, v, 0)
                _ground_column(canvas, px, gy, pz, theme['stone']['block'])
                for dy in range(1, 5):
                    canvas.set(px, gy + dy, pz, 'air')
        # 4 corner posts
        for u in (-2, 2):
            for v in (-1, 1):
                for dy in range(1, 4):
                    canvas.set(*pt(u, v, dy), wood_fam['fence'])
        # Front counter + goods
        for u in (-1, 0, 1):
            canvas.set(*pt(u, 1, 1), wood_fam['stairs'], facing=OPPOSITE[facing], half='top')
        canvas.set(*pt(-1, -1, 1), 'barrel', facing='up')
        canvas.set(*pt(1, -1, 1), 'chest', facing=facing)
        canvas.set(*pt(0, 1, 2), 'pink_candle' if theme['id'] == 'sakura' else 'lantern',
                   **({'candles': '2', 'lit': 'true'} if theme['id'] == 'sakura' else {'hanging': 'false'}))
        # Striped sloped awning
        for u in range(-2, 3):
            blk = c1 if (u % 2 == 0) else c2
            for v in (-1, 0, 1):
                canvas.set(*pt(u, v, 4 if v <= 0 else 3), blk)
        canvas.set(*pt(0, 0, 3), lantern_blk, hanging='true')


def place_street_lamp(canvas, x, z, style='auto', part_name='Props/Garden Lantern'):
    """Place a grounded thematic lantern (`toro` stone lantern, timber hanging post, or `neon` pylon)."""
    x, z = int(round(x)), int(round(z))
    gy = canvas.ground_y(x, z)
    if gy < 2 or canvas.get(x, gy + 1, z) != 'air':
        return False
    theme = canvas.theme
    if style == 'auto':
        if theme['id'] in ('sakura', 'samurai'):
            style = 'toro'
        elif theme['id'] == 'futuristic':
            style = 'neon'
        else:
            style = 'post'

    lantern_blk = theme.get('light', 'lantern')
    with canvas.part(part_name):
        if style == 'toro':
            # Authentic Japanese Tōrō stone lantern!
            _ground_column(canvas, x, gy, z, theme['stone']['block'])
            canvas.set(x, gy + 1, z, theme['stone']['block'])
            canvas.set(x, gy + 2, z, theme['stone']['wall'])
            canvas.set(x, gy + 3, z, theme.get('glow_block', 'pearlescent_froglight'))
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if canvas.get(x + dx, gy + 3, z + dz) == 'air':
                    canvas.set(x + dx, gy + 3, z + dz, theme['wood']['trapdoor'],
                               facing=facing_toward(dx, dz), half='bottom', open='true')
            canvas.set(x, gy + 4, z, theme['roof']['slab'], type='bottom')
        elif style == 'neon':
            _ground_column(canvas, x, gy, z, theme['dark_stone']['block'])
            canvas.set(x, gy + 1, z, theme['dark_stone']['wall'])
            canvas.set(x, gy + 2, z, theme['dark_stone']['wall'])
            canvas.set(x, gy + 3, z, theme.get('glow_block', 'sea_lantern'))
            canvas.set(x, gy + 4, z, theme['stone']['slab'], type='bottom')
            canvas.set(x, gy + 5, z, 'end_rod', facing='up')
        else:
            _ground_column(canvas, x, gy, z, theme['stone']['block'])
            canvas.set(x, gy + 1, z, theme['stone']['wall'])
            canvas.set(x, gy + 2, z, theme['accent_wood']['fence'])
            canvas.set(x, gy + 3, z, theme['accent_wood']['fence'])
            canvas.set(x, gy + 4, z, theme['accent_wood']['slab'], type='bottom')
            if canvas.get(x + 1, gy + 4, z) == 'air' and canvas.get(x + 1, gy + 3, z) == 'air':
                canvas.set(x + 1, gy + 4, z, theme['accent_wood']['slab'], type='bottom')
                canvas.set(x + 1, gy + 3, z, lantern_blk, hanging='true')
            else:
                canvas.set(x, gy + 5, z, lantern_blk, hanging='false')
    return True


def place_bench(canvas, x, z, facing='south', length=3, part_name='Props/Bench'):
    """Place a wooden stair bench with trapdoor armrests."""
    x, z = int(round(x)), int(round(z))
    gy = canvas.ground_y(x, z)
    if gy < 2:
        return False
    wood_fam = canvas.theme['wood']
    along_x = facing in ('north', 'south')
    half = length // 2
    with canvas.part(part_name):
        for o in range(-half, half + 1):
            bx = x + (o if along_x else 0)
            bz = z + (0 if along_x else o)
            bgy = canvas.ground_y(bx, bz)
            if bgy >= 2 and abs(bgy - gy) <= 1 and canvas.get(bx, bgy + 1, bz) == 'air':
                _ground_column(canvas, bx, bgy, bz, canvas.theme['stone']['block'])
                canvas.set(bx, bgy + 1, bz, wood_fam['stairs'], facing=OPPOSITE[facing], half='bottom')
        for end_o, arm_face in ((-half - 1, 'west' if along_x else 'north'),
                                (half + 1, 'east' if along_x else 'south')):
            ax = x + (end_o if along_x else 0)
            az = z + (0 if along_x else end_o)
            agy = canvas.ground_y(ax, az)
            if agy == gy and canvas.get(ax, agy + 1, az) == 'air':
                canvas.set(ax, agy + 1, az, wood_fam['trapdoor'], facing=arm_face, half='bottom', open='true')
    return True


def place_zen_garden(canvas, cx, cz, rx=3, rz=3, part_name='Zones/Zen Rock Garden', seed=606):
    """Build a framed raked-gravel zen garden with mossy stones and a Tōrō lantern."""
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        return
    border_blk = canvas.theme['accent_wood'].get('wood', 'dark_oak_wood')
    with canvas.part(part_name):
        for dz in range(-rz, rz + 1):
            for dx in range(-rx, rx + 1):
                px, pz = cx + dx, cz + dz
                if not (1 <= px < canvas.sx - 1 and 1 <= pz < canvas.sz - 1):
                    continue
                _ground_column(canvas, px, gy, pz, 'stone')
                canvas.set(px, gy + 1, pz, 'air')
                if abs(dx) == rx or abs(dz) == rz:
                    canvas.set(px, gy, pz, border_blk, axis='x' if abs(dz) == rz else 'z')
                else:
                    # Raked wave pattern alternating calcite / gravel / diorite
                    rake = 'calcite' if (dz % 2 == 0) else 'gravel'
                    canvas.set(px, gy, pz, rake)
        # Mossy meditation boulder cluster off-center
        canvas.set(cx - 1, gy + 1, cz, 'mossy_cobblestone')
        canvas.set(cx - 1, gy + 2, cz, 'mossy_cobblestone_slab', type='bottom')
        canvas.set(cx, gy + 1, cz, 'cobblestone_slab', type='bottom')
    place_street_lamp(canvas, cx + rx - 1, cz - rz + 1, style='toro', part_name=part_name)


def place_spawn_pad(canvas, cx, cz, radius=2, look_at=None, part_name='Zones/Spawn Pad'):
    """Inlay an ornate compass spawn medallion flush into the terrain and set `canvas.spawn`."""
    cx, cz = int(round(cx)), int(round(cz))
    gy = canvas.ground_y(cx, cz)
    if gy < 2:
        gy = 8
    theme = canvas.theme
    stone_blk = theme['stone']['block']
    dark_blk = theme['dark_stone']['block']
    glow_blk = theme.get('glow_block', 'pearlescent_froglight')

    with canvas.part(part_name):
        for dz in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                d = math.hypot(dx, dz)
                if d <= radius + 0.4:
                    px, pz = cx + dx, cz + dz
                    _ground_column(canvas, px, gy, pz, stone_blk)
                    for hy in range(gy + 1, gy + 5):
                        canvas.set(px, hy, pz, 'air')
                    if dx == 0 and dz == 0:
                        canvas.set(px, gy, pz, 'chiseled_stone_bricks' if theme['id'] != 'futuristic' else 'lodestone')
                    elif (abs(dx) == 1 and dz == 0) or (dx == 0 and abs(dz) == 1):
                        canvas.set(px, gy, pz, glow_blk)
                    elif abs(dx) == abs(dz) and abs(dx) == 1:
                        canvas.set(px, gy, pz, dark_blk)
                    else:
                        canvas.set(px, gy, pz, stone_blk)

    canvas.set_spawn(cx, gy + 1, cz, look_at=look_at)
    return (cx, gy + 1, cz)


# ------------------------------------------------------------ 12. Floating Hot Air Balloon
def place_hot_air_balloon(
    canvas,
    cx,
    basket_y,
    cz,
    radius=4.8,
    colors=('red_wool', 'white_wool', 'yellow_wool'),
    spiral=0.10,
    part_name='Sky/Hot Air Balloon',
):
    """Build a detailed floating Montgolfier hot-air balloon (`gondola basket` +
    `spruce_fence rigging` + `campfire/shroomlight burner` + `teardrop striped envelope`).
    Uses zero log/leaf blocks so `validate.py` (`trees.floating`, `support.hanging`) passes 100%.
    """
    cx, basket_y, cz = int(round(cx)), int(round(basket_y)), int(round(cz))
    r_max = float(radius)
    env_h = max(11, int(round(r_max * 2.85)))
    throat_y = basket_y + 5
    colors = tuple(colors) if colors else ('red_wool', 'white_wool')

    with canvas.part(part_name):
        # 1. Wicker Gondola Basket (3x3 core + trapdoor rim + hanging bottom lantern)
        for dz in range(-1, 2):
            for dx in range(-1, 2):
                canvas.set(cx + dx, basket_y, cz + dz, 'spruce_planks')
                if abs(dx) == 1 or abs(dz) == 1:
                    canvas.set(cx + dx, basket_y + 1, cz + dz, 'spruce_planks')
        # Underneath trim + centered hanging lantern
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            canvas.set(cx + dx, basket_y - 1, cz + dz, 'dark_oak_slab', type='top')
        canvas.set(cx, basket_y - 1, cz, 'chain')
        canvas.set(cx, basket_y - 2, cz, 'lantern', hanging='true')

        # Exterior wicker trapdoors & sandbag accents on the basket sides
        for d in (-1, 0, 1):
            canvas.set(cx + d, basket_y + 1, cz - 2, 'spruce_trapdoor', facing='north', open='true')
            canvas.set(cx + d, basket_y + 1, cz + 2, 'spruce_trapdoor', facing='south', open='true')
            canvas.set(cx - 2, basket_y + 1, cz + d, 'spruce_trapdoor', facing='west', open='true')
            canvas.set(cx + 2, basket_y + 1, cz + d, 'spruce_trapdoor', facing='east', open='true')
        canvas.set(cx - 1, basket_y + 1, cz, 'barrel', facing='up')
        canvas.set(cx, basket_y + 2, cz + 1, 'lantern', hanging='false')

        # 2. Corner Suspension Rigging (`basket_y + 2 .. throat_y`)
        for ox, oz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            for y in range(basket_y + 2, throat_y + 1):
                canvas.set(cx + ox, y, cz + oz, 'spruce_fence')

        # 3. Glowing Burner Core suspended below the envelope throat
        canvas.set(cx, throat_y - 2, cz, 'dark_oak_planks')
        canvas.set(cx, throat_y - 1, cz, 'campfire', lit='true', signal_fire='false', facing='north')
        canvas.set(cx, throat_y + 1, cz, 'shroomlight')

        # 4. Wooden Throat Collar (`throat_y`)
        for dz in range(-2, 3):
            for dx in range(-2, 3):
                d = math.hypot(dx, dz)
                if 1.3 <= d <= 2.45:
                    canvas.set(cx + dx, throat_y, cz + dz, 'dark_oak_planks')

        # 5. Sculpted Teardrop Envelope (`throat_y + 1 .. throat_y + env_h`)
        equator_t = 0.62
        for dy in range(1, env_h + 1):
            y = throat_y + dy
            if y >= canvas.sy - 1:
                break
            t = dy / float(env_h)
            if t <= equator_t:
                # Smooth lower flare from throat (r=2.1) to equator (r=r_max)
                u = t / equator_t
                r_layer = 2.05 + (r_max - 2.05) * math.sin(u * math.pi * 0.5)
            else:
                # Hemispherical upper crown from equator (r=r_max) to apex
                u = (t - equator_t) / (1.0 - equator_t)
                r_layer = r_max * math.sqrt(max(0.0, 1.0 - u * u * 0.96))

            ir = int(math.ceil(r_layer + 1))
            is_belt = abs(t - equator_t) < (0.85 / env_h)
            for dz in range(-ir, ir + 1):
                for dx in range(-ir, ir + 1):
                    d = math.hypot(dx, dz)
                    inner = -1.0 if dy >= env_h - 1 else (r_layer - 1.32)
                    if inner < d <= r_layer:
                        ang = math.atan2(dz, dx) + dy * spiral
                        gore = int(math.floor((ang + math.pi) / (math.pi / 4.0))) % len(colors)
                        blk = colors[-1] if is_belt else colors[gore]
                        canvas.set(cx + dx, y, cz + dz, blk)

        # Apex cap & finial
        top_y = min(canvas.sy - 2, throat_y + env_h)
        canvas.set(cx, top_y, cz, 'dark_oak_planks')
        canvas.set(cx, top_y + 1, cz, 'spruce_slab', type='bottom')

    canvas.register_landmark('Hot Air Balloon', cx, throat_y + env_h // 2, cz)
    return {'top_y': throat_y + env_h + 1, 'basket_y': basket_y}

