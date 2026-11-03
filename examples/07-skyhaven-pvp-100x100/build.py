#!/usr/bin/env python3
"""Generate `skyhaven-pvp-spawn.nbt` + `.schem` (100x64x100) — Box-Inside-Box Spawn + PvP Zone:
- Centered `50x50` Safezone Spawn (`x=25..74, z=25..74`) outlined by a flush `red_concrete` border:
  - Flattened, airy free-roam courtyard around a central Compass Spawn Gazebo `(50, 11, 50)`
  - Stamped compact medieval houses (`house_188`, `house_212`, `house_65`) & stalls (`stall_01`, `stall_02`)
  - Watertight Crystal Fishing Pond with an arched bridge over it + wooden fishing pier
  - 3 Floating Striped Hot Air Balloons at staggered heights in the sky
  - Custom oak/sakura trees + working wooden chain swing, Wishing Fountain, Campfire healing spot,
    PvP Enchanting/Anvil prep station, small mossy rocks, benches & lanterns
- Outer `100x100` PvP Warzone Ring (`outside x=25..74, z=25..74`):
  - Flat `y=10` fighting floor (~85% open combat space, zero tall-grass hitbox clutter)
  - Flush inlaid stone-brick/prismarine battle lanes, arena ring & 4 corner Duel/KOTH circles
  - 8 outer custom oak trees + sculpted rocks & small boulders for tactical bow cover
- Outer `100x100` Blue Border (`x=0, 99, z=0, 99`):
  - Continuous `blue_concrete` base line topped by a 3-block `blue_stained_glass` arena wall
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from mckit import Canvas, ZoneGrid, mix, props, terrain, trees  # noqa: E402
from mckit.shapes import fbm2d  # noqa: E402
from mckit.palette import rand01  # noqa: E402


ZONE_MAP = """
D W N W D
W G A C W
N R S P N
W T K F W
D W N W D
""".strip()

ZONE_LEGEND = {
    'S': 'Central Spawn Courtyard',
    'G': 'NW Guild Tavern & Stall',
    'A': 'North Free-Roam Lawn',
    'C': 'NE Cottage & Fountain',
    'R': 'West Free-Roam Plaza',
    'P': 'East Pond Overlook',
    'T': 'SW Cottage, Swing & Prep',
    'K': 'South Campfire Nook',
    'F': 'Fishing Pond & Bridge',
    'D': 'PvP Corner Duel Ring',
    'N': 'PvP Cardinal Battle Lane',
    'W': 'PvP Open Warzone Turf',
}


def _set_col(c, x, top_y, z, surface_blk, sub_blk='dirt'):
    """Fill solid terrain crust from `y = 3` up to `top_y`."""
    for y in range(3, top_y + 1):
        if y == top_y:
            c.set(x, y, z, surface_blk)
        elif y >= top_y - 2:
            c.set(x, y, z, sub_blk)
        else:
            c.set(x, y, z, 'stone' if (x + y + z) % 3 else 'andesite')


def build_sculpted_flat_pvp_terrain(c):
    """Build flattened, highly playable terrain:
    - `y = 10` flat across the PvP fighting zone & Safezone free-roam courtyard (`x=5..94, z=5..94`)
    - Gentle `y = 11` 1-block terrace only under NW Guild Hall (`28..44, 28..41`) & NE Cottage (`60..70, 28..36`)
    - Smooth 3-block stadium rim (`y = 11..14`) along the outer 5 blocks (`d_edge <= 4`) meeting the Blue Glass wall
      so `relief_std >= 0.95` while keeping 90%+ of walkable combat & spawn space flat!
    """
    turf_mix = mix({'grass_block': 74, 'moss_block': 18, 'coarse_dirt': 8}, seed=401)
    rim_mix = mix({'grass_block': 52, 'moss_block': 22, 'stone': 14, 'andesite': 12}, seed=402)

    with c.part('Terrain/Arena & Safezone Base'):
        for z in range(100):
            for x in range(100):
                d_edge = min(x, 99 - x, z, 99 - z)
                n = fbm2d(x, z, scale=16.0, octaves=2, seed=77)
                if d_edge == 0:
                    gy = 14
                elif d_edge == 1:
                    gy = 13 + (1 if n > 0.25 else 0)
                elif d_edge == 2:
                    gy = 12 + (1 if n > 0.30 else 0)
                elif d_edge == 3:
                    gy = 11 + (1 if n > 0.35 else 0)
                elif d_edge == 4:
                    gy = 11 if n > -0.15 else 10
                else:
                    gy = 10
                    # Gentle 1-block garden terrace under NW Guild Hall & NE Cottage inside safezone
                    if 27 <= x <= 44 and 27 <= z <= 41:
                        gy = 11
                    elif 60 <= x <= 71 and 27 <= z <= 36:
                        gy = 11

                surf = rim_mix(x, gy, z) if d_edge <= 3 else turf_mix(x, gy, z)
                _set_col(c, x, gy, z, surf)


def inlay_warzone_floor_patterns(c):
    """Inlay 100% flush (`y = 10`) PvP battle lanes, octagonal/circular combat track,
    and 4 corner Duel/KOTH medallions outside the `50x50` Red Line (`25..74`).
    Because `stone_bricks` sits at `y = 10` over `dirt` at `y = 9`, it is completely flat
    underfoot for PvP combat while giving clear visual geometry & cell richness!
    """
    lane_mix = mix({
        'stone_bricks': 46,
        'cracked_stone_bricks': 22,
        'mossy_stone_bricks': 18,
        'polished_andesite': 14,
    }, seed=510)
    ring_mix = mix({
        'stone_bricks': 52,
        'mossy_stone_bricks': 24,
        'chiseled_stone_bricks': 12,
        'polished_andesite': 12,
    }, seed=511)

    pattern_cols = set()

    def set_flush(x, z, blk):
        gy = c.ground_y(x, z)
        c.set(x, gy - 1, z, 'dirt')
        c.set(x, gy, z, blk)
        pattern_cols.add((x, z))

    with c.part('PvPZone/Flush Battle Lanes & Combat Ring'):
        for z in range(4, 96):
            for x in range(4, 96):
                # Stay strictly outside the 50x50 safezone + red border (25..74)
                if 25 <= x <= 74 and 25 <= z <= 74:
                    continue
                if c.ground_y(x, z) != 10:
                    continue

                # 1. Four 4-wide Cardinal PvP Battle Lanes radiating from Safezone exits
                on_ns_lane = (48 <= x <= 51) and (z <= 24 or z >= 75)
                on_ew_lane = (48 <= z <= 51) and (x <= 24 or x >= 75)
                if on_ns_lane or on_ew_lane:
                    edge_trim = x in (48, 51) if on_ns_lane else z in (48, 51)
                    set_flush(x, z, 'spruce_planks' if edge_trim and (x + z) % 4 == 0 else lane_mix(x, 10, z))
                    continue

                # 2. Concentric Warzone Combat Ring (`r = 38.0 .. 40.4` from `(49.5, 49.5)`)
                d_center = math.hypot(x - 49.5, z - 49.5)
                if 37.8 <= d_center <= 40.3:
                    set_flush(x, z, ring_mix(x, 10, z))
                    continue

                # 3. Inner PvP Staging Apron 3 blocks outside the Red Line (`d_box == 3`)
                dx_box = max(25 - x, 0, x - 74)
                dz_box = max(25 - z, 0, z - 74)
                d_box = max(dx_box, dz_box)
                if d_box == 3 and (x + z) % 2 == 0:
                    set_flush(x, z, lane_mix(x, 10, z))

    # 4. Four Corner Duel / KOTH Medallions (`(13,13)`, `(86,13)`, `(13,86)`, `(86,86)`)
    with c.part('PvPZone/Corner Duel Medallions'):
        for mcx, mcz in ((13, 13), (86, 13), (13, 86), (86, 86)):
            for dz in range(-5, 6):
                for dx in range(-5, 6):
                    px, pz = mcx + dx, mcz + dz
                    d = math.hypot(dx, dz)
                    if d <= 5.2 and c.ground_y(px, pz) == 10:
                        if d <= 1.2:
                            c.set(px, 8, pz, 'stone')
                            c.set(px, 9, pz, 'sea_lantern')
                            c.set(px, 10, pz, 'blue_stained_glass')
                        elif 2.6 <= d <= 3.6:
                            set_flush(px, pz, 'dark_prismarine')
                        elif d >= 4.3:
                            set_flush(px, pz, 'chiseled_stone_bricks' if (dx == 0 or dz == 0) else 'stone_bricks')
                        else:
                            set_flush(px, pz, ring_mix(px, 10, pz))
                        pattern_cols.add((px, pz))

    return pattern_cols


def build_free_roam_spawn_courtyard(c):
    """Build an open, flattened compass plaza + central Spawn Gazebo at `(50, 10, 50)`,
    leaving wide-open walkable courtyard & turf around it so players have air to roam.
    """
    plaza_mix = mix({
        'stone_bricks': 44,
        'polished_andesite': 26,
        'cracked_stone_bricks': 16,
        'mossy_stone_bricks': 14,
    }, seed=601)
    occupied = set()

    with c.part('Safezone/Central Compass Courtyard'):
        for dz in range(-8, 9):
            for dx in range(-8, 9):
                d = math.hypot(dx, dz)
                px, pz = 50 + dx, 50 + dz
                if d <= 7.6:
                    c.set(px, 9, pz, 'dirt')
                    if abs(d - 7.0) <= 0.65:
                        c.set(px, 10, pz, 'dark_prismarine' if (dx + dz) % 2 == 0 else 'chiseled_stone_bricks')
                    elif (dx == 0 or dz == 0) and 4 <= max(abs(dx), abs(dz)) <= 6:
                        c.set(px, 10, pz, 'smooth_quartz')
                    else:
                        c.set(px, 10, pz, plaza_mix(px, 10, pz))
                    occupied.add((px, pz))

    # Compact radius=3 Open-Air Spawn Gazebo at `(50, 50)` + exact player spawn pad
    props.place_gazebo(c, cx=50, cz=50, radius=3, part_name='Landmarks/Central Spawn Gazebo')
    c.set_spawn(50, 12, 50, look_at=(74, 15, 50))
    return occupied


def build_wishing_fountain(c, fx, fz, part_name='Safezone/Wishing Fountain'):
    """Build a neat 5x5 watertight stone & froglight fountain inside the safezone."""
    occupied = set()
    fy = c.ground_y(fx, fz)
    with c.part(part_name):
        for dz in range(-2, 3):
            for dx in range(-2, 3):
                px, pz = fx + dx, fz + dz
                occupied.add((px, pz))
                _set_col(c, px, fy, pz, 'stone_bricks')
                if abs(dx) == 2 or abs(dz) == 2:
                    c.set(px, fy + 1, pz, 'stone_bricks')
                    if abs(dx) == 2 and abs(dz) == 2:
                        c.set(px, fy + 2, pz, 'lantern', hanging='false')
                elif dx == 0 and dz == 0:
                    c.set(px, fy, pz, 'sea_lantern')
                    c.set(px, fy + 1, pz, 'stone_bricks')
                    c.set(px, fy + 2, pz, 'stone_brick_wall')
                    c.set(px, fy + 3, pz, 'pearlescent_froglight')
                else:
                    c.set(px, fy, pz, 'prismarine_bricks')
                    c.set(px, fy + 1, pz, 'water')
    return occupied


def build_pvp_gear_prep_station(c, cx, cz, part_name='Safezone/PvP Enchant & Anvil Nook'):
    """Compact outdoor Blacksmith & Enchanting nook near the Red Line so players can
    enchant, repair, and grab Ender-Chest gear before jumping into PvP.
    """
    occupied = set()
    gy = c.ground_y(cx, cz)
    with c.part(part_name):
        for dz in range(-2, 3):
            for dx in range(-3, 4):
                px, pz = cx + dx, cz + dz
                occupied.add((px, pz))
                c.set(px, gy - 1, pz, 'dirt')
                c.set(px, gy, pz, 'stone_bricks' if (dx + dz) % 2 == 0 else 'polished_andesite')
        # Bookshelf L-back + enchanting table + anvil + smithing table + ender chest
        for dx in (-2, -1, 0):
            c.set(cx + dx, gy + 1, cz - 2, 'bookshelf')
            c.set(cx + dx, gy + 2, cz - 2, 'bookshelf' if dx != 0 else 'spruce_slab')
        c.set(cx - 1, gy + 1, cz, 'enchanting_table')
        c.set(cx + 1, gy + 1, cz - 1, 'anvil', facing='south')
        c.set(cx + 2, gy + 1, cz - 1, 'smithing_table')
        c.set(cx + 2, gy + 1, cz + 1, 'ender_chest', facing='west')
        c.set(cx - 2, gy + 1, cz + 1, 'barrel', facing='up')
        c.set(cx - 2, gy + 2, cz + 1, 'lantern', hanging='false')
        # Neat open timber awning posts
        for ox, oz in ((-3, -2), (3, -2)):
            for dy in range(1, 4):
                c.set(cx + ox, gy + dy, cz + oz, 'spruce_fence')
            c.set(cx + ox, gy + 4, cz + oz, 'spruce_slab', type='bottom')
    return occupied


def build_cozy_healing_campfire(c, cx, cz, part_name='Safezone/Campfire Rest Nook'):
    """Compact open-air campfire & log bench circle inside the South Safezone."""
    occupied = set()
    gy = c.ground_y(cx, cz)
    with c.part(part_name):
        for dz in range(-3, 4):
            for dx in range(-3, 4):
                if math.hypot(dx, dz) <= 3.2:
                    px, pz = cx + dx, cz + dz
                    occupied.add((px, pz))
                    c.set(px, gy, pz, 'coarse_dirt' if (dx + dz) % 2 == 0 else 'podzol')
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            c.set(cx + dx, gy, cz + dz, 'cobblestone')
        c.set(cx, gy, cz, 'cobblestone')
        c.set(cx, gy + 1, cz, 'campfire', lit='true', signal_fire='false', facing='north')
        # Log benches around the fire
        for dx in (-1, 0, 1):
            c.set(cx + dx, gy + 1, cz + 3, 'stripped_spruce_log', axis='x')
            c.set(cx + dx, gy + 1, cz - 3, 'stripped_spruce_log', axis='x')
        c.set(cx + 3, gy + 1, cz, 'barrel', facing='up')
        c.set(cx + 3, gy + 2, cz, 'lantern', hanging='false')
    return occupied


def build_border_markers(c):
    """Add crisp PvP threshold corner/exit marker posts on the `50x50` Red Line and
    glowing Blue Stained-Glass Pylons along the outer `100x100` Blue Border.
    """
    with c.part('Borders/Safezone Red Marker Posts'):
        # 4 corners of the 50x50 Red Safezone + 8 cardinal exit threshold posts
        red_posts = [
            (25, 25), (74, 25), (25, 74), (74, 74),
            (47, 25), (52, 25), (47, 74), (52, 74),
            (25, 47), (25, 52), (74, 47), (74, 52),
        ]
        for px, pz in red_posts:
            gy = c.ground_y(px, pz)
            c.set(px, gy, pz, 'red_concrete')
            c.set(px, gy + 1, pz, 'red_concrete')
            c.set(px, gy + 2, pz, 'polished_deepslate_wall')
            c.set(px, gy + 3, pz, 'lantern', hanging='false')

    with c.part('Borders/Warzone Blue Glass Pylons'):
        # Sleek blue pylons every ~25 blocks along the outer 100x100 Blue Glass Wall
        coords = (0, 25, 49, 74, 99)
        pylons = set()
        for v in coords:
            pylons.update([(v, 0), (v, 99), (0, v), (99, v)])
        for px, pz in sorted(pylons):
            # Find highest blue_stained_glass or blue_concrete in column
            top_y = c.top(px, pz)
            if top_y >= 10:
                c.set(px, top_y, pz, 'blue_concrete')
                c.set(px, top_y + 1, pz, 'polished_deepslate_wall')
                c.set(px, top_y + 2, pz, 'soul_lantern', hanging='false')


def build():
    c = Canvas(100, 64, 100, theme='vanilla_plus')
    c.zones = ZoneGrid(100, 100, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

    # ------------------------------------------------------------ 1. Flattened Playable Terrain
    build_sculpted_flat_pvp_terrain(c)

    # ------------------------------------------------------------ 2. Safezone Fishing Pond (`SE` of 50x50)
    pond = terrain.carve_pond(
        c,
        center=(63, 62),
        rx=6.8,
        rz=5.8,
        depth=3,
        water_y=9,
        lily_density=0.10,
        reeds=True,
        stepping_stones=[(59, 58), (61, 57)],
        part_name='Safezone/Crystal Fishing Pond',
        seed=701,
    )
    water_y = pond['water_y']

    # ------------------------------------------------------------ 3. Safezone Courtyard & Paths + Warzone Floor Pattern
    occupied = set()
    occupied |= build_free_roam_spawn_courtyard(c)
    pvp_pattern_cols = inlay_warzone_floor_patterns(c)

    path_mix = mix({
        'stone_bricks': 34,
        'polished_andesite': 24,
        'gravel': 22,
        'coarse_dirt': 20,
    }, seed=705)
    path_cols = set()
    safezone_paths = [
        # 4 Cardinal Safezone Avenues from Spawn Courtyard (50,50) to the 4 Red-Line Exits
        ([(50, 43), (50, 34), (50, 26)], 2.1, 'Paths/North Safezone Path'),
        ([(50, 57), (50, 66), (50, 73)], 2.1, 'Paths/South Safezone Path'),
        ([(43, 50), (34, 50), (26, 50)], 2.1, 'Paths/West Safezone Path'),
        ([(57, 50), (63, 50), (73, 50)], 2.1, 'Paths/East Safezone Path'),
        # Gentle branches to Pond Bridge, NW Guild Hall, NE Cottage & SW Prep Nook
        ([(55, 53), (60, 55), (63, 55)], 1.7, 'Paths/Pond Bridge Spur'),
        ([(46, 46), (41, 43), (36, 41)], 1.7, 'Paths/NW Guild Spur'),
        ([(54, 46), (59, 41), (63, 36)], 1.7, 'Paths/NE Cottage Spur'),
        ([(46, 54), (42, 58), (36, 63)], 1.7, 'Paths/SW Cottage Spur'),
    ]
    for pts, w, pname in safezone_paths:
        path_cols |= terrain.lay_path(c, pts, width=w, material_mix=path_mix, part_name=pname, seed=710 + len(path_cols))

    # ------------------------------------------------------------ 4. Arched Pond Bridge + Fishing Pier + Safezone Features
    props.place_bridge(
        c,
        p_start=(63, 10, 55),
        p_end=(63, 10, 69),
        arch_height=2.6,
        half_width=1,
        part_name='Safezone/Pond Arched Bridge',
    )
    props.place_dock(
        c,
        start_xz=(55, 62),
        dir_dx=1,
        dir_dz=0,
        length=4,
        half_width=1,
        water_y=water_y,
        part_name='Safezone/Fishing Pier',
    )

    occupied |= build_wishing_fountain(c, 65, 43)
    occupied |= build_pvp_gear_prep_station(c, 42, 57)
    occupied |= build_cozy_healing_campfire(c, 42, 67)

    # ------------------------------------------------------------ 5. Stamped Houses & Stalls Inside 50x50 Safezone
    # Compact assets leaving generous open free-roam space around `(50, 50)`:
    c.stamp('houses/house_188', 35, 34, rotate=0, sink=1, ground_fill='stone_bricks', part_name='Safezone/NW Guild Tavern')
    c.stamp('houses/house_212', 66, 31, rotate=180, sink=1, ground_fill='stone_bricks', part_name='Safezone/NE Keeper Cottage')
    c.stamp('houses/house_65', 32, 67, rotate=90, sink=1, ground_fill='stone_bricks', part_name='Safezone/SW Brick Cottage')
    c.stamp('stalls/stall_02', 32, 45, rotate=90, sink=0, ground_fill='stone_bricks', part_name='Safezone/West Merchant Stall')
    c.stamp('stalls/stall_01', 58, 31, rotate=180, sink=0, ground_fill='stone_bricks', part_name='Safezone/North Bakery Stall')

    # ------------------------------------------------------------ 6. Safezone Trees, Tree Swing & Small Rocks
    # Custom hand-crafted trees tucked cleanly inside the 50x50 safezone
    safezone_trees = [
        ('trees_oak/oak_12', 45, 31, 90, 'Safezone/North Courtyard Oak'),
        ('trees_oak/oak_36', 69, 39, 180, 'Safezone/East Meadow Oak'),
    ]
    for tid, tx, tz, rot, pname in safezone_trees:
        c.stamp(tid, tx, tz, rotate=rot, anchor='trunk', sink=1, ground_fill='oak_wood', part_name=pname)
    trees.place_tree(
        c, x=68, z=53, species='sakura', scale=0.88,
        hang_lanterns=2, part_name='Safezone/Pond Cherry Blossom', seed=802,
    )

    # Custom Oak with Working Hanging Chain Swing in SW Safezone Lawn
    sw_tree = trees.place_tree(
        c, x=31, z=56, species='giant_oak', scale=0.88,
        with_swing_branch=True, hang_lanterns=2,
        part_name='Safezone/SW Swing Oak', seed=801,
    )
    if sw_tree.get('swing'):
        props.place_swing(c, sw_tree['swing'], part_name='Safezone/Hanging Tree Swing')

    # Small mossy rocks around the free-roam safezone & pond bank
    safezone_rocks = [
        (40, 46, 1.3), (58, 46, 1.3), (45, 61, 1.2), (54, 68, 1.4),
        (69, 69, 1.5), (57, 56, 1.2), (28, 52, 1.3), (60, 38, 1.2),
    ]
    for idx, (rx_, rz_, rad) in enumerate(safezone_rocks):
        terrain.place_boulder(c, rx_, rz_, radius=rad, mossy=True, part_name='Safezone/Small Rocks', seed=820 + idx)

    # Benches & street lamps inside the 50x50 safezone
    for bx, bz, fac in ((45, 48, 'south'), (55, 48, 'south'), (48, 55, 'east'), (58, 66, 'east')):
        props.place_bench(c, x=bx, z=bz, facing=fac, length=3, part_name='Safezone/Courtyard Benches')
    for lx, lz in ((46, 44), (54, 44), (46, 56), (54, 56), (50, 33), (50, 67), (33, 50), (68, 48)):
        props.place_street_lamp(c, lx, lz, style='post', part_name='Safezone/Lantern Posts')

    # Light wildflower scatter ONLY inside the 50x50 Safezone (`27..72`) so PvP stays hitbox-clean!
    terrain.scatter_flora(
        c,
        bounds=(27, 27, 72, 72),
        density=0.18,
        excluded_cols=path_cols | occupied | pond['water_cells'],
        part_name='Safezone/Meadow Wildflowers',
        seed=850,
    )

    # ------------------------------------------------------------ 7. Outer 100x100 PvP Warzone Trees & Rocks
    # Simple, balanced tactical cover in the outer PvP ring (~85% wide-open fighting space!)
    warzone_trees = [
        ('trees_oak/oak_12', 10, 31, 0, 'PvPZone/NW Flank Oak'),
        ('trees_oak/oak_24', 31, 10, 90, 'PvPZone/North West Oak'),
        ('trees_oak/oak_36', 68, 10, 180, 'PvPZone/North East Oak'),
        ('trees_oak/oak_48', 89, 31, 270, 'PvPZone/NE Flank Oak'),
        ('trees_oak/oak_36', 10, 68, 90, 'PvPZone/SW Flank Oak'),
        ('trees_oak/oak_12', 31, 89, 0, 'PvPZone/South West Oak'),
        ('trees_oak/oak_48', 68, 89, 270, 'PvPZone/South East Oak'),
        ('trees_oak/oak_24', 89, 68, 180, 'PvPZone/SE Flank Oak'),
    ]
    for tid, tx, tz, rot, pname in warzone_trees:
        c.stamp(tid, tx, tz, rotate=rot, anchor='trunk', sink=1, ground_fill='oak_wood', part_name=pname)

    # 4 low sculpted rock outcrops + 20 small mossy rocks for PvP bow-cover
    warzone_outcrops = [
        ('rocks/rock_09', 15, 44, 0, 'PvPZone/West Lane Rock'),
        ('rocks/rock_09', 84, 55, 90, 'PvPZone/East Lane Rock'),
        ('rocks/rock_10', 43, 14, 180, 'PvPZone/North Lane Crag'),
        ('rocks/rock_10', 56, 85, 270, 'PvPZone/South Lane Crag'),
    ]
    for rid, rx_, rz_, rot, pname in warzone_outcrops:
        c.stamp(rid, rx_, rz_, rotate=rot, sink=1, ground_fill='stone', part_name=pname)

    warzone_boulders = [
        (19, 20, 1.5), (80, 20, 1.5), (20, 80, 1.5), (80, 80, 1.5),
        (8, 49, 1.6), (91, 49, 1.6), (49, 8, 1.6), (49, 91, 1.6),
        (17, 36, 1.3), (17, 63, 1.3), (82, 36, 1.3), (82, 63, 1.3),
        (36, 17, 1.3), (63, 17, 1.3), (36, 82, 1.3), (63, 82, 1.3),
        (22, 10, 1.4), (77, 10, 1.4), (22, 89, 1.4), (77, 89, 1.4),
    ]
    for idx, (bx, bz, rad) in enumerate(warzone_boulders):
        terrain.place_boulder(c, bx, bz, radius=rad, mossy=(idx % 2 == 0), part_name='PvPZone/Tactical Boulders', seed=900 + idx)

    # Clean Warzone lighting posts along battle lanes & duel corners
    warzone_lamps = [
        (46, 14), (53, 14), (46, 85), (53, 85),
        (14, 46), (14, 53), (85, 46), (85, 53),
        (19, 13), (13, 19), (80, 13), (86, 19),
        (19, 86), (13, 80), (80, 86), (86, 80),
        (21, 30), (78, 30), (21, 69), (78, 69),
    ]
    for lx, lz in warzone_lamps:
        props.place_street_lamp(c, lx, lz, style='post', part_name='PvPZone/Warzone Lanterns')

    # ------------------------------------------------------------ 8. Floating Hot Air Balloons in the Sky!
    props.place_hot_air_balloon(
        c, cx=36, basket_y=31, cz=46, radius=4.8,
        colors=('red_wool', 'white_wool', 'yellow_wool'),
        spiral=0.08, part_name='Sky/Crimson Gold Hot Air Balloon',
    )
    props.place_hot_air_balloon(
        c, cx=64, basket_y=35, cz=56, radius=5.0,
        colors=('cyan_wool', 'white_wool', 'light_blue_wool'),
        spiral=-0.08, part_name='Sky/Azure Sky Hot Air Balloon',
    )
    props.place_hot_air_balloon(
        c, cx=53, basket_y=39, cz=31, radius=4.4,
        colors=('orange_wool', 'white_wool', 'lime_wool'),
        spiral=0.10, part_name='Sky/Sunburst Hot Air Balloon',
    )

    # ------------------------------------------------------------ 9. Box-Inside-Box Borders (Red 50x50 + Blue Glass 100x100)
    # Inner 50x50 Safezone Red Line Border (`x=25..74, z=25..74`, flush `raised=0` so PvP entry is 100% walkable!)
    terrain.draw_border(
        c,
        block='red_concrete',
        width=1,
        raised=0,
        bounds=(25, 25, 74, 74),
        part_name='Borders/Safezone 50x50 Red Line',
    )
    # Outer 100x100 PvP Arena Blue Line + 3-Block Blue Stained Glass Wall (`x=0..99, z=0..99`)
    terrain.draw_border(
        c,
        block='blue_concrete',
        width=1,
        raised=1,
        bounds=(0, 0, 99, 99),
        glass_block='blue_stained_glass',
        glass_height=3,
        part_name='Borders/Warzone 100x100 Blue Glass Border',
    )
    build_border_markers(c)

    # Custom showcase cameras for inspecting both the full 100x100 box-in-box AND close-ups of the 50x50 & balloons
    c.add_camera('safezone-closeup', position=[32, 30, 82], target=[52, 16, 48], fov=52, lighting='golden')
    c.add_camera('pond-and-balloons', position=[86, 24, 84], target=[52, 26, 46], fov=58, lighting='day')
    c.add_camera('pvp-border-view', position=[16, 24, 84], target=[45, 12, 54], fov=52, lighting='day')

    out_nbt = os.path.join(HERE, 'skyhaven-pvp-spawn.nbt')
    out_schem = os.path.join(HERE, 'skyhaven-pvp-spawn.schem')
    res = c.save(out_nbt, schem_path=out_schem)
    print('Saved %s & %s: %d blocks (%.1f KB)' % (res['nbt'], res['schem'], res['blocks'], res['bytes'] / 1024.0))
    return res


if __name__ == '__main__':
    build()
