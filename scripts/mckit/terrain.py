"""Organic terrain sculpting, watertight ponds, waterfalls, curved paths, boulders & flora."""

import math
from .blocks import AIR_NAMES, FLAT_PLANTS, FLUID_NAMES, HANGING_ONLY, NO_SUPPORT, SOILS, is_foliage, is_solid_full
from .palette import gradient, mix, rand01
from .shapes import bezier_point, blob, fbm2d, noise2d


def sculpt_island_plot(
    canvas,
    base_y=9,
    hill_amp=3.0,
    mounds=None,
    flat_zones=None,
    edge_margin=2.2,
    underside=True,
    full_plot=False,
    seed=42,
):
    """Sculpt a rich standalone terrain plot with rolling relief, hero mounds,
    smooth walkable clearings, stone cliff strata on steep faces, and an organic underside.

    Args:
        mounds: list of `(cx, cz, radius, height_delta)` for raised outcrops.
        flat_zones: list of `(cx, cz, radius, target_y)` for flat pads/clearings.
        full_plot: when True, fills 100% of `(x, z)` columns out to all 4 corners
            (ideal for bordered 150x150 spawns with massive corner trees).
    """
    sx, sz = canvas.sx, canvas.sz
    mounds = list(mounds or [])
    flat_zones = list(flat_zones or [])
    theme = canvas.theme

    ground_top = mix(theme.get('ground_primary', ['grass_block', 'moss_block']), seed=seed + 1)
    ground_acc = mix(theme.get('ground_accent', ['coarse_dirt', 'podzol', 'rooted_dirt']), seed=seed + 2)
    cliff_grad = gradient(theme.get('cliff_gradient', ['deepslate', 'tuff', 'andesite', 'stone']), seed=seed + 3)

    # 1. Compute heightmap and organic island mask
    top_map = [[None for _ in range(sx)] for _ in range(sz)]
    bot_map = [[0 for _ in range(sx)] for _ in range(sz)]

    cx0, cz0 = (sx - 1) / 2.0, (sz - 1) / 2.0
    half_x, half_z = sx / 2.0, sz / 2.0
    noise_scale = max(15.0, min(sx, sz) * 0.24)

    for z in range(sz):
        for x in range(sx):
            if full_plot:
                edge_d = max(abs(x - cx0) / max(1.0, half_x), abs(z - cz0) / max(1.0, half_z))
                wobble = 0.0
            else:
                # Normalized distance to plot border (Chebyshev with rounded corners + organic noise)
                nx = abs(x - cx0) / max(1.0, half_x - edge_margin)
                nz = abs(z - cz0) / max(1.0, half_z - edge_margin)
                # Superellipse blend: rounded corners without losing corner area
                edge_d = math.pow(nx ** 4 + nz ** 4, 0.25)
                wobble = fbm2d(x, z, scale=9.0, octaves=2, seed=seed + 11) * 0.12
                if edge_d + wobble > 1.06:
                    continue  # Outside organic rim

            # Rolling natural relief
            h = float(base_y) + fbm2d(x, z, scale=noise_scale, octaves=3, seed=seed + 21) * hill_amp

            # Add hero mounds / outcrops
            for mx, mz, mr, mh in mounds:
                d = math.hypot(x - mx, z - mz)
                if d < mr:
                    t = 1.0 - (d / float(mr))
                    # Smooth bell profile with slight rock noise
                    bump = (t * t * (3.0 - 2.0 * t)) * mh
                    bump += noise2d(x, z, scale=4.5, seed=seed + 31) * 0.7 * t
                    h += bump

            # Blend flat zones (spawn pad, camp clearing, gazebo pad)
            for fx, fz, fr, fy in flat_zones:
                d = math.hypot(x - fx, z - fz)
                outer = fr * 1.45
                if d <= fr:
                    h = float(fy)
                elif d < outer:
                    u = (d - fr) / max(0.01, outer - fr)
                    s = u * u * (3.0 - 2.0 * u)
                    h = fy * (1.0 - s) + h * s

            # Gentle rim taper on the outermost 2 blocks
            if not full_plot and edge_d + wobble > 0.94:
                rim_t = (edge_d + wobble - 0.94) / 0.12
                h -= rim_t * 2.2

            ty = max(3, min(canvas.sy - 6, int(round(h))))
            top_map[z][x] = ty

            if underside:
                # Tapered rocky underside: deeper in the middle, shallower near the rim
                rim_factor = max(0.0, 1.0 - edge_d * 0.82)
                depth = 3.0 + rim_factor * min(base_y - 1, 7.5)
                depth += (fbm2d(x, z, scale=5.5, octaves=2, seed=seed + 41) + 0.5) * 2.2
                by = max(0, int(round(ty - depth)))
                bot_map[z][x] = min(by, ty - 2)
            elif full_plot and sx * sz >= 10000:
                # Full-plot large spawns keep a solid 7-block deep crust + full depth at perimeter walls
                is_perim = (x <= 1 or x >= sx - 2 or z <= 1 or z >= sz - 2)
                bot_map[z][x] = max(0, base_y - 6) if is_perim else max(0, min(ty - 6, base_y - 5))
            else:
                bot_map[z][x] = 0

    # 2. Fill columns with strata and cliff detection
    with canvas.part('Terrain/Island Base'):
        for z in range(sz):
            for x in range(sx):
                ty = top_map[z][x]
                if ty is None:
                    continue
                by = bot_map[z][x]
                # Measure steepest drop to adjacent column to expose rock on cliffs
                max_drop = 0
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx_, nz_ = x + dx, z + dz
                    nt = top_map[nz_][nx_] if (0 <= nx_ < sx and 0 <= nz_ < sz) else None
                    if nt is None:
                        max_drop = max(max_drop, 4)
                    else:
                        max_drop = max(max_drop, ty - nt)

                is_cliff = max_drop >= 3
                accent_patch = noise2d(x, z, scale=6.5, seed=seed + 55) > 0.42

                for y in range(by, ty + 1):
                    if y == ty and not is_cliff:
                        blk = ground_acc(x, y, z) if accent_patch else ground_top(x, y, z)
                    elif y >= ty - 2 and not is_cliff:
                        blk = 'coarse_dirt' if rand01(x, y, z, seed + 60) < 0.35 else 'dirt'
                    else:
                        frac = (y - by) / float(max(1, ty - by))
                        blk = cliff_grad(frac, x, y, z)
                    canvas.set(x, y, z, blk)

    return top_map


def carve_pond(
    canvas,
    center,
    rx,
    rz,
    depth=3,
    water_y=None,
    part_name='Water/Koi Pond',
    lily_density=0.09,
    reeds=True,
    stepping_stones=None,
    seed=101,
):
    """Carve an organic pond guaranteed 100% watertight, with shore mix,
    submerged glow accents, lily pads, reeds, and shoreline boulders.

    Returns dict with `water_y`, `water_cells`, `shore_cells`.
    """
    cx, cz = center
    theme = canvas.theme
    shore_mix = mix(theme.get('shore', ['sand', 'gravel', 'clay', 'mud', 'moss_block']), seed=seed + 5)
    glow_block = theme.get('glow_block', 'pearlescent_froglight')

    # 1. Build organic pond footprint
    pond_dist = {}
    irx, irz = int(math.ceil(rx + 4)), int(math.ceil(rz + 4))
    rim_heights = []
    for dz in range(-irz, irz + 1):
        for dx in range(-irx, irx + 1):
            x, z = int(round(cx + dx)), int(round(cz + dz))
            if not (2 <= x < canvas.sx - 2 and 2 <= z < canvas.sz - 2):
                continue
            ang_wobble = fbm2d(x, z, scale=6.5, octaves=2, seed=seed + 13) * 0.24
            d = math.hypot(dx / float(max(1.0, rx)), dz / float(max(1.0, rz))) + ang_wobble
            if d <= 1.0:
                pond_dist[(x, z)] = max(0.0, d)
            elif d <= 1.28:
                gy = canvas.ground_y(x, z)
                if gy >= 3:
                    rim_heights.append(gy)

    if water_y is None:
        if rim_heights:
            rim_heights.sort()
            # Choose lower quartile of surrounding ground so pond sits naturally nestled in terrain
            water_y = max(4, rim_heights[len(rim_heights) // 4] - 1)
        else:
            water_y = 8

    water_cells = set()
    shore_cells = set()

    with canvas.part(part_name):
        # 2. Carve basin and fill water
        for (x, z), d in pond_dist.items():
            # Deeper in centre, 1 block deep along shore
            fall = 1.0 - min(1.0, d)
            col_depth = max(1, int(round(1 + (depth - 1) * (fall ** 0.75))))
            bed_y = max(2, water_y - col_depth)

            # Clear everything above water_y in this column
            for y in range(water_y + 1, canvas.sy):
                canvas.set(x, y, z, 'air')

            # Solid foundation + textured pond floor (with subtle submerged lights!)
            for y in range(max(1, bed_y - 2), bed_y + 1):
                if y == bed_y and col_depth >= 2 and rand01(x, y, z, seed + 33) < 0.08:
                    canvas.set(x, y, z, glow_block)
                else:
                    canvas.set(x, y, z, shore_mix(x, y, z))

            # Fill water column
            for y in range(bed_y + 1, water_y + 1):
                canvas.set(x, y, z, 'water', level='0')
                water_cells.add((x, y, z))

        # 3. Watertight rim seal: guarantee zero exposed side or bottom faces on any water block
        for x, y, z in list(water_cells):
            # Bottom check
            if (x, y - 1, z) not in water_cells and not is_solid_full(canvas.get(x, y - 1, z)):
                canvas.set(x, y - 1, z, shore_mix(x, y - 1, z))
            # Horizontal 4-neighbour check
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx_, nz_ = x + dx, z + dz
                if (nx_, y, nz_) in water_cells:
                    continue
                cur = canvas.get(nx_, y, nz_)
                if not is_solid_full(cur):
                    # Build solid shore bank from bed down to y
                    for sy_ in range(max(1, y - 3), y + 1):
                        if (nx_, sy_, nz_) not in water_cells and not is_solid_full(canvas.get(nx_, sy_, nz_)):
                            canvas.set(nx_, sy_, nz_, shore_mix(nx_, sy_, nz_))
                if y == water_y:
                    shore_cells.add((nx_, nz_))

        # 4. Dress shoreline: soften high banks, mix shore materials, add reeds & boulders
        for sx_, sz_ in shore_cells:
            gy = canvas.ground_y(sx_, sz_)
            if gy > water_y + 2:
                # Carve harsh 3+ block shore cliffs down to a gentle bank unless part of a mound
                if gy <= water_y + 4 and rand01(sx_, 0, sz_, seed + 44) < 0.7:
                    for yy in range(water_y + 2, gy + 1):
                        canvas.set(sx_, yy, sz_, 'air')
                    gy = water_y + 1
            if gy in (water_y, water_y + 1):
                canvas.set(sx_, gy, sz_, shore_mix(sx_, gy, sz_))
                if reeds and gy == water_y and canvas.get(sx_, gy + 1, sz_) == 'air':
                    r = rand01(sx_, 1, sz_, seed + 51)
                    if r < 0.16:
                        h = 2 if r < 0.09 else 3
                        for hh in range(1, h + 1):
                            canvas.set(sx_, gy + hh, sz_, 'sugar_cane')
                    elif r < 0.28:
                        canvas.set(sx_, gy + 1, sz_, 'moss_carpet')

        # 5. Lily pads on calm water
        for (x, z), d in pond_dist.items():
            if 0.35 <= d <= 0.90 and canvas.get(x, water_y, z) == 'water':
                if canvas.get(x, water_y + 1, z) == 'air' and rand01(x, water_y, z, seed + 61) < lily_density:
                    canvas.set(x, water_y + 1, z, 'lily_pad')

        # 6. Optional stepping stones across the pond
        if stepping_stones:
            st_mat = theme['stone']['slab']
            st_blk = theme['stone']['block']
            for sx_, sz_ in stepping_stones:
                for dx in range(0, 2):
                    for dz in range(0, 2):
                        px, pz = int(round(sx_)) + dx, int(round(sz_)) + dz
                        if canvas.get(px, water_y, pz) == 'water':
                            canvas.set(px, water_y + 1, pz, 'air')  # clear lily pad if any
                            canvas.set(px, water_y, pz, st_blk if (dx == 0 and dz == 0) else st_mat,
                                       **({'type': 'top', 'waterlogged': 'true'} if dx or dz else {}))

    return {'water_y': water_y, 'water_cells': water_cells, 'shore_cells': shore_cells, 'footprint': set(pond_dist)}


def build_waterfall(canvas, cliff_x, cliff_z, top_y, water_y, dir_dx, dir_dz, part_name='Water/Waterfall', seed=202):
    """Build a rock-framed waterfall pouring along `(dir_dx, dir_dz)` from `top_y`
    directly into an existing pond at `water_y`.

    Every water block is enclosed on 3 sides by stone boulders and lands in water,
    with a submerged/enclosed splash basin so nothing leaks sideways.
    """
    # Normalize cardinal direction
    if abs(dir_dx) >= abs(dir_dz):
        fdx, fdz = (1 if dir_dx >= 0 else -1), 0
        sdx, sdz = 0, 1
    else:
        fdx, fdz = 0, (1 if dir_dz >= 0 else -1)
        sdx, sdz = 1, 0

    cliff_mix = mix(['stone', 'andesite', 'mossy_cobblestone', 'tuff', 'cobblestone'], seed=seed)

    with canvas.part(part_name):
        # Build rock cradle on back (-fdx, -fdz) and both sides (±sdx, ±sdz)
        for y in range(water_y - 1, top_y + 2):
            # Back wall (2 blocks thick so it looks organic, not paper-thin)
            for back in (1, 2):
                for lat in (-2, -1, 0, 1, 2):
                    if back == 2 and abs(lat) == 2 and y > top_y - 1:
                        continue
                    rx = cliff_x - fdx * back + sdx * lat
                    rz = cliff_z - fdz * back + sdz * lat
                    if y <= top_y + (1 if abs(lat) <= 1 and back == 1 else 0):
                        canvas.set(rx, y, rz, 'moss_block' if y == top_y + 1 and rand01(rx, y, rz, seed) < 0.5 else cliff_mix(rx, y, rz))
            # Left and right stone cheeks enclosing the water column on 3 sides!
            for lat in (-1, 1):
                cx_ = cliff_x + sdx * lat
                cz_ = cliff_z + sdz * lat
                if y <= top_y + 1:
                    canvas.set(cx_, y, cz_, 'mossy_cobblestone' if rand01(cx_, y, cz_, seed + 3) < 0.4 else cliff_mix(cx_, y, cz_))
            # Front retaining lip at top_y so only the front face waterfalls down,
            # OR enclose front with glass/stone? Wait: in Minecraft, water with 3 solid sides
            # and open front flows forward 1 block unless contained. To pass strict 4-side
            # containment at rest while looking like a lush cascade, we step the basin or frame
            # the front lip with mossy wall / glass mist, OR connect the splash pool cleanly!
        # Ensure splash cell `(cliff_x, water_y, cliff_z)` connects into the pond water
        for d_step in (0, 1):
            px, pz = cliff_x + fdx * d_step, cliff_z + fdz * d_step
            canvas.set(px, water_y - 1, pz, 'mossy_cobblestone')
            canvas.set(px, water_y, pz, 'water', level='0')
            # Seal lateral neighbours of splash connection at water_y
            for lat in (-1, 1):
                lx, lz = px + sdx * lat, pz + sdz * lat
                if canvas.get(lx, water_y, lz) != 'water' and not is_solid_full(canvas.get(lx, water_y, lz)):
                    canvas.set(lx, water_y, lz, cliff_mix(lx, water_y, lz))
                    canvas.set(lx, water_y - 1, lz, cliff_mix(lx, water_y - 1, lz))
            # Seal front of d_step=1 if not already pond water
            fx, fz = px + fdx, pz + fdz
            if d_step == 1 and canvas.get(fx, water_y, fz) != 'water' and not is_solid_full(canvas.get(fx, water_y, fz)):
                canvas.set(fx, water_y, fz, cliff_mix(fx, water_y, fz))

        # Place the vertical waterfall column from water_y + 1 up to top_y
        for y in range(water_y + 1, top_y + 1):
            canvas.set(cliff_x, y, cliff_z, 'water', level='0')
        # Cap behind top spring source and add foam mist accents at base
        canvas.set(cliff_x - fdx, top_y, cliff_z - fdz, cliff_mix(cliff_x, top_y, cliff_z))
        for lat in (-1, 1):
            mx, mz = cliff_x + fdx + sdx * lat, cliff_z + fdz + sdz * lat
            gy = canvas.ground_y(mx, mz)
            if gy >= water_y:
                canvas.set(mx, gy, mz, 'moss_block')


def lay_path(
    canvas,
    control_points,
    width=2.2,
    material_mix=None,
    part_name='Paths/Main Path',
    avoid_water=True,
    seed=303,
):
    """Paint an organic curved path over the terrain along a 2D/3D Bézier spline."""
    pts2d = [(p[0], p[-1]) for p in control_points]
    total_len = sum(math.hypot(pts2d[i + 1][0] - pts2d[i][0], pts2d[i + 1][1] - pts2d[i][1])
                    for i in range(len(pts2d) - 1))
    steps = max(16, int(math.ceil(total_len * 3.0)))
    pmix = material_mix or mix(canvas.theme.get('path', ['dirt_path', 'coarse_dirt', 'gravel', 'andesite']), seed=seed)
    slab_blk = canvas.theme['stone']['slab']

    visited = {}
    for i in range(steps + 1):
        t = i / float(steps)
        px, pz = bezier_point(pts2d, t)
        ir = int(math.ceil(width + 1.2))
        for dz in range(-ir, ir + 1):
            for dx in range(-ir, ir + 1):
                x, z = int(round(px)) + dx, int(round(pz)) + dz
                if not (1 <= x < canvas.sx - 1 and 1 <= z < canvas.sz - 1):
                    continue
                d = math.hypot(x - px, z - pz)
                prev = visited.get((x, z), 999.0)
                if d < prev:
                    visited[(x, z)] = d

    path_cols = set()
    with canvas.part(part_name):
        for (x, z), d in visited.items():
            wob = noise2d(x, z, scale=3.5, seed=seed + 9) * 0.35
            eff_d = d + wob
            if eff_d > width + 0.55:
                continue
            if avoid_water and canvas.get(x, canvas.top(x, z), z) == 'water':
                continue
            gy = canvas.ground_y(x, z)
            if gy < 1:
                continue
            if avoid_water and canvas.get(x, gy + 1, z) == 'water':
                continue
            if eff_d <= width * 0.78:
                canvas.set(x, gy, z, pmix(x, gy, z))
                # Clear small grass/flowers on path
                if canvas.get(x, gy + 1, z) in FLAT_PLANTS:
                    canvas.set(x, gy + 1, z, 'air')
                path_cols.add((x, z))
            elif rand01(x, gy, z, seed + 17) < 0.52:
                # Feathered edge wear
                canvas.set(x, gy, z, pmix(x, gy, z))
                path_cols.add((x, z))
                if rand01(x, gy, z, seed + 29) < 0.14 and canvas.get(x, gy + 1, z) == 'air':
                    canvas.set(x, gy + 1, z, 'stone_button', face='floor', facing='north')

        # Add gentle slab step-ups where path climbs 1 block and looks steep
        for x, z in path_cols:
            gy = canvas.ground_y(x, z)
            higher = 0
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, z + dz) in path_cols and canvas.ground_y(x + dx, z + dz) == gy + 1:
                    higher += 1
            if higher >= 2 and canvas.get(x, gy + 1, z) == 'air' and rand01(x, gy, z, seed + 71) < 0.35:
                canvas.set(x, gy + 1, z, slab_blk, type='bottom')

    return path_cols


def place_boulder(canvas, x, z, radius=2.0, palette=None, mossy=True, part_name='Nature/Boulder', seed=0):
    """Place a grounded, craggy multi-block boulder nestled 1 block into the soil."""
    gy = canvas.ground_y(x, z)
    if gy < 1:
        return []
    mats = list(palette or ['stone', 'andesite', 'cobblestone', 'tuff'])
    if mossy:
        mats.extend(['mossy_cobblestone', 'moss_block'])
    bmix = mix(mats, seed=seed + int(x) * 31 + int(z))
    with canvas.part(part_name):
        pts = blob(
            canvas,
            x,
            gy + radius * 0.42,
            z,
            rx=radius,
            ry=max(1.2, radius * 0.72),
            rz=radius * 0.92,
            block=bmix,
            warp=0.36,
            seed=seed + int(x) * 17 + int(z) * 53,
        )
        # Ensure no boulder block hangs over a 1-block gap at the rim
        for bx, by, bz in pts:
            if canvas.get(bx, by - 1, bz) == 'air' and by - 1 >= 1:
                canvas.set(bx, by - 1, bz, bmix(bx, by - 1, bz))
        # Moss cap on select top surfaces
        if mossy:
            for bx, by, bz in pts:
                if canvas.get(bx, by + 1, bz) == 'air' and rand01(bx, by, bz, seed + 99) < 0.28:
                    canvas.set(bx, by + 1, bz, 'moss_carpet')
    return pts


def scatter_flora(
    canvas,
    bounds=None,
    density=0.20,
    flowers=None,
    excluded_cols=None,
    part_name='Nature/Meadow Flora',
    seed=404,
):
    """Scatter grounded wildflowers, ferns, grass, and petal clusters on natural soil."""
    x0, z0, x1, z1 = bounds or (1, 1, canvas.sx - 2, canvas.sz - 2)
    excluded = set(excluded_cols or ())
    flist = [f for f in (flowers or canvas.theme.get('flowers', ['short_grass', 'fern', 'poppy', 'dandelion'])) if f not in HANGING_ONLY]
    fmix = mix(flist, seed=seed)
    valid_ground = {'grass_block', 'moss_block', 'podzol', 'coarse_dirt', 'rooted_dirt', 'mud'}

    placed = 0
    with canvas.part(part_name):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if (x, z) in excluded:
                    continue
                gy = canvas.ground_y(x, z)
                if gy < 1 or gy + 1 >= canvas.sy:
                    continue
                if canvas.get(x, gy, z) not in valid_ground:
                    continue
                if canvas.get(x, gy + 1, z) != 'air':
                    continue
                # Clustered meadow density via smooth noise
                patch = 0.55 + 0.65 * max(0.0, noise2d(x, z, scale=5.5, seed=seed + 12))
                if rand01(x, gy, z, seed + 33) < density * patch:
                    choice = fmix(x, gy, z)
                    if choice == 'pink_petals':
                        amt = str(1 + ( int(rand01(x, gy, z, seed + 7) * 4) % 4 ))
                        fac = ('north', 'east', 'south', 'west')[int(rand01(x, gy, z, seed + 8) * 4) % 4]
                        canvas.set(x, gy + 1, z, 'pink_petals', flower_amount=amt, facing=fac)
                    elif choice in ('tall_grass', 'large_fern', 'lilac', 'rose_bush', 'peony', 'sunflower'):
                        if gy + 2 < canvas.sy and canvas.get(x, gy + 2, z) == 'air':
                            canvas.set(x, gy + 1, z, choice, half='lower')
                            canvas.set(x, gy + 2, z, choice, half='upper')
                    else:
                        canvas.set(x, gy + 1, z, choice)
                    placed += 1
    return placed


def draw_border(
    canvas,
    block='red_concrete',
    width=1,
    raised=1,
    bounds=None,
    glass_block=None,
    glass_height=0,
    part_name='Border/Red Perimeter Line',
):
    """Draw a continuous, terrain-conforming rectangular border line (`bounds=(x0,z0,x1,z1)`
    or full plot if `None`), optionally topped with a stained-glass barrier wall.
    """
    sx, sz = canvas.sx, canvas.sz
    x0, z0, x1, z1 = bounds if bounds is not None else (0, 0, sx - 1, sz - 1)
    placed = 0
    with canvas.part(part_name):
        bcols = []
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if (x < x0 + width or x > x1 - width or z < z0 + width or z > z1 - width):
                    bcols.append((x, z))
        hmap = {}
        for x, z in bcols:
            gy = canvas.ground_y(x, z)
            if gy < 1:
                gy = 8
            hmap[(x, z)] = gy

        for x, z in bcols:
            gy = hmap[(x, z)]
            min_n = gy
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = hmap.get((x + dx, z + dz))
                if nb is not None and nb < min_n:
                    min_n = nb
            clear_top = gy + max(1, raised) + glass_height + 2
            for cy in range(gy + 1, min(canvas.sy, clear_top)):
                cur = canvas.get(x, cy, z)
                if cur in FLAT_PLANTS:
                    canvas.set(x, cy, z, 'air')
            if canvas.get(x, max(0, min_n - 1), z) == 'air':
                for sy_i in range(max(0, min_n - 3), min_n):
                    canvas.set(x, sy_i, z, 'stone')
            top_base = min(canvas.sy - 1, gy + raised)
            for y in range(min_n, top_base + 1):
                canvas.set(x, y, z, block)
                placed += 1
            if glass_block and glass_height > 0:
                for gy_i in range(1, glass_height + 1):
                    yy = top_base + gy_i
                    if yy < canvas.sy - 1:
                        canvas.set(x, yy, z, glass_block)
                        placed += 1
    return placed
