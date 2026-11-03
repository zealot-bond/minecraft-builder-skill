#!/usr/bin/env python3
"""Production-Ready 150x150 Full Server Spawn: Grand Haven Sanctuary.

Features:
  - 150x150 full-plot sculpted landscape (`150 x 96 x 150`) with continuous `red_concrete` border
  - Central Spawn Compass Plaza & 8-Pillar Vaulted Crown Rotunda at `(75, 13, 75)` + 4 Plaza Fountains
  - 34x28 Emerald Fishing Lake with 5-wide Arched Bridge over it, Cliff Waterfall & 2 Fishing Piers
  - Colossal 47–74 block Massive Corner Trees in all 4 corners + companion groves & 4 Tree Swings
  - North Guild Keep Citadel + Diorite/Prismarine Guild Manors & Watchtower (`all-builds.zip`)
  - West Artisan Village (5 Medieval Townhouses/Inns + all 5 Market Stalls from `all-builds.zip`)
  - South-West Twin Campfire Camps (tents, cooking spits, benches) & South Thatched Homestead Farms
  - Hand-sculpted rock outcrops (`assets/rocks/*`) + 36 small mossy boulders across shores & trails
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'scripts')))

from mckit import Canvas, ZoneGrid, mix, props, terrain, trees
from mckit.blocks import facing_toward

ZONE_MAP = """
N G K W E
V M A O P
V M S B P
T C R L H
Q C F F Z
"""

ZONE_LEGEND = {
    'N': 'NW Giant Tree',
    'G': 'West Keep Manor',
    'K': 'North Guild Keep',
    'W': 'Waterfall Crag',
    'E': 'NE Giant Tree',
    'V': 'Artisan Village',
    'M': 'Market Square',
    'A': 'North Avenue',
    'O': 'Overlook Gazebo',
    'P': 'Fishing Lake Shore',
    'S': 'Central Spawn',
    'B': 'Pond & Bridge',
    'T': 'Swing Grove',
    'C': 'Campfire Camp',
    'R': 'South Promenade',
    'L': 'South Pier Cove',
    'H': 'Angler Cottage',
    'Q': 'SW Giant Tree',
    'F': 'Homestead Farms',
    'Z': 'SE Giant Tree',
}


def _ground_col(c, x, top_y, z, blk):
    for y in range(int(top_y), 0, -1):
        cur = c.get(x, y, z)
        if y < int(top_y) and cur not in ('air', 'water', 'short_grass', 'fern', 'tall_grass'):
            break
        c.set(x, y, z, blk)


def build_central_spawn_rotunda(c, cx=75, cz=75, base_y=12):
    """Build a monumental 23x23 Central Spawn Compass Plaza + open 8-Pillar Crown Rotunda
    and 4 corner watertight stone fountains.
    """
    occupied = set()
    pave_mix = mix({
        'stone_bricks': 5,
        'polished_andesite': 3,
        'mossy_stone_bricks': 2,
        'cracked_stone_bricks': 1,
        'tuff_bricks': 2,
    }, seed=777)

    with c.part('Landmarks/Central Spawn Plaza'):
        # 1. Circular 25-diameter paved plaza terrace with stone-brick border steps
        plaza_r = 12.5
        for dz in range(-14, 15):
            for dx in range(-14, 15):
                d = math.hypot(dx, dz)
                if d > plaza_r + 1.2:
                    continue
                px, pz = cx + dx, cz + dz
                occupied.add((px, pz))
                # Clear air above plaza
                for cy_ in range(base_y + 1, base_y + 28):
                    c.set(px, cy_, pz, 'air')
                if d <= plaza_r:
                    # Ornate compass star inlay
                    adx, adz = abs(dx), abs(dz)
                    if adx == 0 and adz == 0:
                        blk = 'lodestone'
                    elif (adx == 0 and adz <= 9) or (adz == 0 and adx <= 9):
                        blk = 'smooth_quartz' if (adx + adz) % 3 != 0 else 'chiseled_stone_bricks'
                    elif adx == adz and adx <= 6:
                        blk = 'polished_deepslate'
                    elif abs(d - 5.0) < 0.65 or abs(d - 10.5) < 0.65:
                        blk = 'polished_deepslate'
                    elif (adx, adz) in ((2, 0), (0, 2), (4, 4), (9, 0), (0, 9)):
                        blk = 'verdant_froglight'
                    else:
                        blk = pave_mix(px, base_y, pz)
                    _ground_col(c, px, base_y, pz, blk)
                else:
                    # Stepped outer curb
                    gy = c.ground_y(px, pz)
                    if gy < base_y:
                        _ground_col(c, px, base_y - 1, pz, 'stone_bricks')
                        c.set(px, base_y, pz, 'stone_brick_slab', type='bottom')

    with c.part('Landmarks/Central Crown Rotunda'):
        # 2. 8 Octagonal Pillars at radius ~8 leaving 5-wide cardinal avenues open!
        pillar_offsets = [
            (-3, -8), (3, -8),
            (8, -3), (8, 3),
            (3, 8), (-3, 8),
            (-8, 3), (-8, -3),
        ]
        wall_top = base_y + 7
        for ox, oz in pillar_offsets:
            px, pz = cx + ox, cz + oz
            # Stepped stone plinth
            for bdx, bdz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if bdx == 0 and bdz == 0:
                    c.set(px, base_y + 1, pz, 'chiseled_stone_bricks')
                    c.set(px, base_y + 2, pz, 'stone_bricks')
                else:
                    if c.get(px + bdx, base_y + 1, pz + bdz) == 'air':
                        c.set(px + bdx, base_y + 1, pz + bdz, 'stone_brick_stairs',
                              facing=facing_toward(-bdx, -bdz), half='bottom')
            for y in range(base_y + 3, wall_top + 1):
                c.set(px, y, pz, 'stripped_spruce_wood')
            c.set(px, wall_top + 1, pz, 'chiseled_stone_bricks')

        # 3. Diagonal Crate / Info Kiosk Counters in the 4 diagonal bays
        diag_crates = [
            (-5, -5, 'south', 'ender_chest'),
            (5, -5, 'south', 'chest'),
            (5, 5, 'north', 'ender_chest'),
            (-5, 5, 'north', 'chest'),
        ]
        for ox, oz, fac, crate_blk in diag_crates:
            kx, kz = cx + ox, cz + oz
            c.set(kx, base_y + 1, kz, 'polished_deepslate')
            c.set(kx, base_y + 2, kz, crate_blk, facing=fac)
            c.set(kx + (1 if ox < 0 else -1), base_y + 1, kz, 'spruce_stairs', facing=fac, half='top')
            c.set(kx + (1 if ox < 0 else -1), base_y + 2, kz, 'lantern', hanging='false')

        # 4. Ring Beam + Cardinal Archways at y = wall_top..wall_top+1
        ring_r = 8.4
        for dz in range(-9, 10):
            for dx in range(-9, 10):
                d = math.hypot(dx, dz)
                if 7.4 <= d <= 9.0:
                    c.set(cx + dx, wall_top + 1, cz + dz, 'spruce_wood')
                    if abs(dx) <= 2 or abs(dz) <= 2:
                        # High open cardinal portal arch
                        if abs(dx) == 2 or abs(dz) == 2:
                            c.set(cx + dx, wall_top, cz + dz, 'spruce_stairs',
                                  facing=facing_toward(-dx if abs(dx) == 2 else 0, -dz if abs(dz) == 2 else 0),
                                  half='top')
                    else:
                        c.set(cx + dx, wall_top, cz + dz, 'dark_oak_fence')

        # Hanging warm lanterns around the octagonal ring
        for ox, oz in ((0, -8), (0, 8), (-8, 0), (8, 0), (-6, -6), (6, -6), (-6, 6), (6, 6)):
            if c.get(cx + ox, wall_top + 1, cz + oz) != 'air':
                c.set(cx + ox, wall_top, cz + oz, 'chain')
                c.set(cx + ox, wall_top - 1, cz + oz, 'lantern', hanging='true')

        # 5. Tier 1 Sweeping Dark-Prismarine & Spruce Dome Roof
        dome_base = wall_top + 2
        for layer, r in enumerate((10.0, 8.8, 7.6, 6.4, 5.2)):
            yy = dome_base + layer
            ir = int(math.ceil(r + 1))
            for dz in range(-ir, ir + 1):
                for dx in range(-ir, ir + 1):
                    d = math.hypot(dx, dz)
                    if r - 1.35 <= d <= r:
                        is_trim = (layer == 0 and d >= r - 0.65)
                        blk = 'spruce_slab' if is_trim else 'dark_prismarine'
                        if is_trim:
                            c.set(cx + dx, yy, cz + dz, 'spruce_slab', type='top')
                        else:
                            c.set(cx + dx, yy, cz + dz, blk)
                    elif d < r - 1.35 and layer == 4:
                        c.set(cx + dx, yy, cz + dz, 'spruce_planks')

        # 6. Upper Lantern Cupola + Spire (`y = dome_base + 5 .. +16`)
        cup_y = dome_base + 5
        for ox, oz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            for dy in range(4):
                c.set(cx + ox, cup_y + dy, cz + oz, 'stripped_spruce_wood')
        for dz in range(-3, 4):
            for dx in range(-3, 4):
                if abs(dx) == 3 or abs(dz) == 3:
                    c.set(cx + dx, cup_y + 3, cz + dz, 'spruce_wood')
        # Glowing beacon heart inside cupola
        for dy in range(1, 4):
            c.set(cx, cup_y + dy, cz, 'pearlescent_froglight')
        # Cupola pointed roof + finial spire
        for layer, r in enumerate((4.6, 3.4, 2.3, 1.3)):
            yy = cup_y + 4 + layer
            ir = int(math.ceil(r + 1))
            for dz in range(-ir, ir + 1):
                for dx in range(-ir, ir + 1):
                    if math.hypot(dx, dz) <= r:
                        c.set(cx + dx, yy, cz + dz, 'dark_prismarine' if layer < 3 else 'spruce_wood')
        spire_base = cup_y + 8
        c.set(cx, spire_base, cz, 'stone_brick_wall')
        c.set(cx, spire_base + 1, cz, 'spruce_fence')
        c.set(cx, spire_base + 2, cz, 'chain')
        c.set(cx, spire_base + 3, cz, 'pearlescent_froglight')
        c.set(cx, spire_base + 4, cz, 'end_rod', facing='up')

        # Central hanging chandelier above the spawn medallion (ample headroom y = base_y + 7!)
        ch_top = dome_base + 3
        for y in range(ch_top, base_y + 7, -1):
            c.set(cx, y, cz, 'chain')
        c.set(cx, base_y + 7, cz, 'pearlescent_froglight')
        for dx, dz, fac in ((1, 0, 'east'), (-1, 0, 'west'), (0, 1, 'south'), (0, -1, 'north')):
            c.set(cx + dx, base_y + 7, cz + dz, 'spruce_trapdoor', facing=fac, open='true')
        c.set(cx, base_y + 6, cz, 'lantern', hanging='true')

    # 7. Four Watertight Plaza Fountains flanking the Compass Plaza
    with c.part('Props/Plaza Fountains'):
        for fx, fz in ((61, 61), (89, 61), (61, 89), (89, 89)):
            fy = c.ground_y(fx, fz)
            for dz in range(-2, 3):
                for dx in range(-2, 3):
                    px, pz = fx + dx, fz + dz
                    occupied.add((px, pz))
                    _ground_col(c, px, fy, pz, 'stone_bricks')
                    if abs(dx) == 2 or abs(dz) == 2:
                        # Watertight solid stone-brick rim around water at fy + 1!
                        c.set(px, fy + 1, pz, 'polished_andesite' if (abs(dx) == 2 and abs(dz) == 2) else 'stone_bricks')
                        if abs(dx) == 2 and abs(dz) == 2:
                            c.set(px, fy + 2, pz, 'lantern')
                    elif dx == 0 and dz == 0:
                        c.set(px, fy, pz, 'sea_lantern')
                        c.set(px, fy + 1, pz, 'chiseled_stone_bricks')
                        c.set(px, fy + 2, pz, 'stone_brick_wall')
                        c.set(px, fy + 3, pz, 'verdant_froglight')
                    else:
                        c.set(px, fy, pz, 'prismarine_bricks')
                        c.set(px, fy + 1, pz, 'water')

    c.set_spawn(cx, base_y + 1, cz, look_at=(113, 14, 76))
    c.register_landmark('Central Spawn Rotunda', cx, base_y + 6, cz)
    return occupied


def build_wheat_farm_patch(c, cx, cz, rx=7, rz=5, part_name='Zones/Homestead Wheat Fields'):
    """Build a framed, irrigated golden wheat & hay-bale farm terrace."""
    occupied = set()
    gy = c.ground_y(cx, cz)
    if gy < 2:
        return occupied
    with c.part(part_name):
        for dz in range(-rz - 1, rz + 2):
            for dx in range(-rx - 1, rx + 2):
                px, pz = cx + dx, cz + dz
                occupied.add((px, pz))
                if abs(dx) == rx + 1 or abs(dz) == rz + 1:
                    _ground_col(c, px, gy, pz, 'stripped_oak_wood')
                    if (dx + dz) % 3 == 0 and abs(dx) != 0 and abs(dz) != 0:
                        c.set(px, gy + 1, pz, 'oak_fence')
                        if abs(dx) == rx + 1 and abs(dz) == rz + 1:
                            c.set(px, gy + 2, pz, 'lantern')
                elif dz == 0 and abs(dx) <= rx - 1:
                    # Sealed irrigation trough
                    _ground_col(c, px, gy - 1, pz, 'stone_bricks')
                    c.set(px, gy, pz, 'water')
                    if dx % 4 == 0:
                        c.set(px, gy + 1, pz, 'spruce_slab', type='top')
                else:
                    _ground_col(c, px, gy, pz, 'farmland', )
                    c.set(px, gy, pz, 'farmland', moisture='7')
                    c.set(px, gy + 1, pz, 'wheat', age='7')
        # Stacked hay bales at one corner
        for hdx, hdz, hh in ((-rx + 1, -rz + 1, 2), (-rx + 2, -rz + 1, 1), (-rx + 1, -rz + 2, 1)):
            for dy in range(1, hh + 1):
                c.set(cx + hdx, gy + dy, cz + hdz, 'hay_block', axis='y')
    return occupied


def build():
    c = Canvas(150, 96, 150, theme='vanilla_plus')
    c.zones = ZoneGrid(150, 150, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

    # ------------------------------------------------------------ 1. Sculpt Full 150x150 Terrain
    terrain.sculpt_island_plot(
        c,
        base_y=11,
        hill_amp=2.6,
        mounds=[
            (75, 20, 26.0, 6.2),    # North Citadel & Guild Keep plateau
            (114, 42, 18.0, 5.5),   # NE Waterfall headwater crag & Gazebo bluff
            (18, 18, 22.0, 4.0),    # NW Corner Monarch Tree hill
            (132, 18, 22.0, 4.5),   # NE Corner Monarch Tree hill
            (18, 132, 22.0, 3.8),   # SW Corner Monarch Tree hill
            (132, 132, 22.0, 3.8),  # SE Corner Monarch Tree hill
        ],
        flat_zones=[
            (75, 75, 16.0, 12),     # Central Spawn Plaza & Rotunda
            (75, 20, 14.0, 17),     # North Guild Keep courtyard
            (46, 20, 11.0, 15),     # NW Guild Manor terrace
            (108, 44, 8.0, 16),     # NE Overlook Gazebo terrace
            (26, 48, 11.0, 12),     # West Artisan Village North
            (26, 76, 11.0, 11),     # West Artisan Village South
            (48, 62, 10.0, 11),     # Market Square North
            (48, 86, 10.0, 11),     # Market Square South
            (38, 118, 12.0, 11),    # SW Campfire Sanctuary
            (75, 126, 15.0, 11),    # South Homestead & Farmhouses
            (118, 112, 10.0, 11),   # SE Angler's Cottage clearing
        ],
        underside=False,
        full_plot=True,
        seed=2026150,
    )

    # ------------------------------------------------------------ 2. Emerald Fishing Lake + Waterfall
    pond = terrain.carve_pond(
        c,
        center=(113, 76),
        rx=14.5,
        rz=13.0,
        depth=3,
        water_y=10,
        lily_density=0.08,
        reeds=True,
        stepping_stones=[(106, 68), (109, 66), (118, 84), (121, 82)],
        part_name='Water/Emerald Fishing Lake',
        seed=501,
    )
    water_y = pond['water_y']

    # Roaring Cliff Waterfall tumbling South from the NE bluff (y=16) into the Fishing Lake (y=10)
    terrain.build_waterfall(
        c,
        cliff_x=114,
        cliff_z=60,
        top_y=16,
        water_y=water_y,
        dir_dx=0,
        dir_dz=1,
        part_name='Water/Highland Waterfall',
        seed=502,
    )

    # ------------------------------------------------------------ 3. Grand Road & Avenue Network
    path_cols = set()
    # 4 Cardinal Avenues from Central Spawn (75, 75)
    path_cols |= terrain.lay_path(c, [(75, 62), (75, 45), (75, 29)], width=3.2, part_name='Paths/North Citadel Avenue', seed=601)
    path_cols |= terrain.lay_path(c, [(75, 88), (75, 106), (75, 122)], width=3.0, part_name='Paths/South Homestead Avenue', seed=602)
    path_cols |= terrain.lay_path(c, [(88, 76), (98, 76)], width=3.2, part_name='Paths/East Angler Promenade', seed=603)
    path_cols |= terrain.lay_path(c, [(62, 75), (50, 75), (38, 75)], width=3.2, part_name='Paths/West Market Avenue', seed=604)

    # Lake Loop Road connecting Central Spawn -> North Shore -> Bridge -> South Shore -> Angler Cove
    path_cols |= terrain.lay_path(c, [(94, 76), (98, 62), (113, 59), (128, 64), (132, 76)], width=2.4, part_name='Paths/North Lake Loop', seed=605)
    path_cols |= terrain.lay_path(c, [(94, 76), (98, 90), (113, 93), (126, 92), (132, 76)], width=2.4, part_name='Paths/South Lake Loop', seed=606)
    path_cols |= terrain.lay_path(c, [(75, 46), (94, 45), (106, 45)], width=2.2, part_name='Paths/Overlook Trail', seed=607)

    # Village, Market, Campfire & Corner Sanctuary Trails
    path_cols |= terrain.lay_path(c, [(48, 75), (48, 52), (46, 28)], width=2.5, part_name='Paths/Market Street North', seed=608)
    path_cols |= terrain.lay_path(c, [(48, 75), (46, 98), (40, 114)], width=2.5, part_name='Paths/Campfire Trail', seed=609)
    path_cols |= terrain.lay_path(c, [(40, 118), (58, 122), (75, 120), (98, 118), (114, 112)], width=2.3, part_name='Paths/Southern Rim Road', seed=610)
    path_cols |= terrain.lay_path(c, [(46, 24), (28, 24)], width=2.0, part_name='Paths/NW Grove Path', seed=611)
    path_cols |= terrain.lay_path(c, [(108, 42), (126, 28)], width=2.0, part_name='Paths/NE Grove Path', seed=612)
    path_cols |= terrain.lay_path(c, [(36, 120), (24, 126)], width=2.0, part_name='Paths/SW Grove Path', seed=613)
    path_cols |= terrain.lay_path(c, [(120, 114), (128, 124)], width=2.0, part_name='Paths/SE Grove Path', seed=614)

    # ------------------------------------------------------------ 4. Central Spawn + Fishing Bridge + Piers + Landmarks
    path_cols |= build_central_spawn_rotunda(c, cx=75, cz=75, base_y=12)

    # 4 Cardinal Entry Gates framing Central Spawn
    props.place_torii_gate(c, cx=75, cz=56, axis='x', half_span=4, height=8, part_name='Architecture/North Plaza Arch')
    props.place_torii_gate(c, cx=75, cz=94, axis='x', half_span=4, height=8, part_name='Architecture/South Plaza Arch')
    props.place_torii_gate(c, cx=93, cz=76, axis='z', half_span=4, height=8, part_name='Architecture/East Lake Arch')
    props.place_torii_gate(c, cx=57, cz=75, axis='z', half_span=4, height=8, part_name='Architecture/West Market Arch')

    # Grand 5-Wide Arched Bridge soaring North-South across the Emerald Fishing Lake!
    bridge = props.place_bridge(
        c,
        p_start=(113, 11, 61),
        p_end=(113, 11, 91),
        arch_height=4.6,
        half_width=2,
        part_name='Architecture/Grand Fishing Pond Bridge',
    )
    path_cols |= bridge['deck_cols']

    # Twin Wooden Fishing Piers jutting into the West & East coves of the pond
    props.place_dock(c, start_xz=(99, 76), dir_dx=1, dir_dz=0, length=6, half_width=1, water_y=water_y, part_name='Architecture/West Angler Pier')
    props.place_dock(c, start_xz=(127, 74), dir_dx=-1, dir_dz=0, length=6, half_width=1, water_y=water_y, part_name='Architecture/East Boathouse Pier')

    # North Guild Keep Citadel (`+32y` prominence) + Overlook Gazebo + Zen Courtyard
    props.place_pagoda(c, cx=75, cz=18, tiers=3, base_half=5, part_name='Landmarks/North Guild Keep')
    props.place_gazebo(c, cx=108, cz=44, radius=4, part_name='Architecture/Waterfall Overlook Gazebo')
    props.place_zen_garden(c, cx=96, cz=32, rx=4, rz=4, part_name='Zones/Citadel Zen Courtyard', seed=701)

    # ------------------------------------------------------------ 5. Stamp Hand-Built Homes & Stalls (`all-builds.zip`)
    house_placements = [
        # North Citadel Guild Manors & Watchtower
        ('houses/house_193', 46, 20, 90, 'stone_bricks', 'Village/NW Guild Manor Tower'),
        ('houses/house_157', 96, 18, 270, 'stone_bricks', 'Village/NE Citadel Watchhouse'),
        # West Artisan Village Townhouses & Timber Inns
        ('houses/house_73', 24, 46, 90, 'stone_bricks', 'Village/North Brick Townhouse'),
        ('houses/house_85', 24, 74, 90, 'cobblestone', 'Village/Artisan Timber Inn'),
        ('houses/house_61', 26, 96, 0, 'stone_bricks', 'Village/Weaver Cottage'),
        ('houses/house_133', 46, 42, 180, 'cobblestone', 'Village/Blacksmith Forge'),
        # South Homestead Thatched Farmhouse & Barn + SE Angler's Cottage
        ('houses/house_217', 62, 130, 0, 'stone_bricks', 'Homestead/Thatched Farmhouse'),
        ('houses/house_229', 94, 130, 0, 'stone_bricks', 'Homestead/Harvest Barn'),
        ('houses/house_145', 118, 112, 270, 'cobblestone', 'Lakeside/Angler Cottage'),
    ]
    for hid, hx, hz, rot, gfill, pname in house_placements:
        st = c.stamp(hid, hx, hz, rotate=rot, sink=0, ground_fill=gfill, part_name=pname)
        path_cols |= st['occupied']

    # Stamp all 5 Hand-Built Market Stalls from `valturystallfreepack.schem` around Market Square & Lake!
    stall_placements = [
        ('stalls/stall_01', 44, 62, 90, 'Market/Baker Stall'),
        ('stalls/stall_02', 53, 62, 270, 'Market/Apothecary Stall'),
        ('stalls/stall_03', 44, 86, 90, 'Market/Merchant Cart'),
        ('stalls/stall_04', 53, 86, 270, 'Market/Armorer Stall'),
        ('stalls/stall_05', 102, 95, 0, 'Lakeside/Fishmonger Stall'),
    ]
    for sid, sx_, sz_, rot, pname in stall_placements:
        st = c.stamp(sid, sx_, sz_, rotate=rot, sink=0, ground_fill='cobblestone', part_name=pname)
        path_cols |= st['occupied']

    # Extra colorful lakeside & plaza kiosks
    props.place_market_stall(c, cx=124, cz=95, facing='north', color_pair=('blue_wool', 'white_wool'), part_name='Lakeside/Tackle Kiosk')
    props.place_market_stall(c, cx=56, cz=52, facing='south', color_pair=('yellow_wool', 'white_wool'), part_name='Market/Produce Kiosk')

    # ------------------------------------------------------------ 6. Campfire Sanctuary & Homestead Wheat Terraces
    camp1 = props.place_campfire_camp(c, cx=38, cz=118, radius=6.0, tents=2, part_name='Zones/SW Adventurer Camp', seed=801)
    camp2 = props.place_campfire_camp(c, cx=22, cz=112, radius=4.8, tents=1, part_name='Zones/West Ranger Campfire', seed=802)
    path_cols |= camp1.get('occupied', set()) | camp2.get('occupied', set())

    path_cols |= build_wheat_farm_patch(c, cx=78, cz=132, rx=7, rz=4, part_name='Homestead/East Wheat Terrace')
    path_cols |= build_wheat_farm_patch(c, cx=78, cz=114, rx=6, rz=4, part_name='Homestead/North Wheat Terrace')

    # ------------------------------------------------------------ 7. Massive Corner Trees + Custom Groves + Swings
    # 4 Colossal Hand-Crafted Corner Monarchs (47–74 blocks tall!) + Companion Corner Trees
    corner_trees = [
        # NW Corner Sanctuary
        ('trees_assorted/tree_05', 23, 23, 0, 'Corners/NW Monarch World-Tree'),
        ('trees_oak/oak_02', 37, 13, 90, 'Corners/NW Companion Oak'),
        ('trees_oak/oak_14', 13, 37, 180, 'Corners/NW Ridge Oak'),
        # NE Corner Sanctuary
        ('trees_assorted/tree_06', 129, 20, 90, 'Corners/NE Monarch Forest Giant'),
        ('trees_oak/oak_37', 115, 14, 0, 'Corners/NE Golden Canopy Oak'),
        ('trees_oak/oak_26', 136, 36, 270, 'Corners/NE Bluff Oak'),
        # SW Corner Sanctuary
        ('trees_assorted/tree_12', 21, 129, 180, 'Corners/SW Monarch Canopy Tree'),
        ('trees_oak/oak_49', 36, 136, 90, 'Corners/SW Giant Blossom Oak'),
        ('trees_oak/oak_03', 13, 114, 0, 'Corners/SW Overlook Oak'),
        # SE Corner Sanctuary
        ('trees_oak/oak_01', 132, 132, 270, 'Corners/SE Monarch Moss Oak'),
        ('trees_oak/oak_25', 114, 136, 90, 'Corners/SE Meadow Giant Oak'),
        ('trees_oak/oak_50', 136, 112, 180, 'Corners/SE Lakeside Blossom Oak'),
        # Mid-district accent custom oaks from `60_oak_tree_pack`
        ('trees_oak/oak_12', 58, 36, 0, 'Nature/Citadel Slope Oak West'),
        ('trees_oak/oak_36', 90, 38, 90, 'Nature/Citadel Slope Oak East'),
        ('trees_oak/oak_48', 58, 104, 180, 'Nature/South Promenade Oak West'),
        ('trees_oak/oak_58', 92, 104, 270, 'Nature/South Promenade Sakura'),
        ('trees_oak/oak_24', 138, 60, 0, 'Nature/East Lake Shore Oak North'),
        ('trees_oak/oak_15', 138, 92, 90, 'Nature/East Lake Shore Oak South'),
    ]
    for tid, tx, tz, rot, pname in corner_trees:
        c.stamp(tid, tx, tz, rotate=rot, anchor='trunk', sink=1, ground_fill='oak_wood', part_name=pname)

    # Procedural Trees with 4 Working Wooden Chain Swings + Lakeside Weeping Willows!
    swing_specs = [
        (16, 94, 'giant_oak', 1.15, 901, 'Nature/West Swing Oak', 'Props/Swing Grove Oak Swing'),
        (54, 122, 'sakura', 1.08, 902, 'Nature/Camp Blossom Swing Tree', 'Props/Camp Sakura Swing'),
        (98, 54, 'sakura', 1.05, 903, 'Nature/North Pond Swing Tree', 'Props/Pond Overlook Swing'),
        (104, 126, 'giant_oak', 1.10, 904, 'Nature/Homestead Swing Oak', 'Props/Homestead Oak Swing'),
    ]
    for sx_, sz_, sp, sc, sd, tpart, spart in swing_specs:
        t_info = trees.place_tree(c, x=sx_, z=sz_, species=sp, scale=sc, with_swing_branch=True, hang_lanterns=2, part_name=tpart, seed=sd)
        if t_info.get('swing'):
            props.place_swing(c, t_info['swing'], part_name=spart)

    # Weeping Willows & Bonsai Pines framing the Emerald Fishing Lake
    trees.place_tree(c, x=126, z=60, species='weeping_willow', scale=1.05, hang_lanterns=2, part_name='Nature/Lake Willow NE', seed=910)
    trees.place_tree(c, x=100, z=88, species='weeping_willow', scale=1.00, hang_lanterns=2, part_name='Nature/Lake Willow SW', seed=911)
    trees.place_tree(c, x=122, z=48, species='japanese_pine', scale=1.00, hang_lanterns=2, part_name='Nature/Waterfall Bonsai Pine', seed=912)
    trees.place_bamboo_clump(c, x=136, z=50, radius=3.8, stalks=16, part_name='Nature/Lakeside Bamboo Grove', seed=913)

    # ------------------------------------------------------------ 8. Small Rocks & Sculpted Outcrops
    # Stamp hand-sculpted rock formations from `10_free_rock.schem`
    rock_assets = [
        ('rocks/rock_07', 106, 56, 0, 'Rocks/Waterfall West Crag'),
        ('rocks/rock_08', 121, 56, 90, 'Rocks/Waterfall East Crag'),
        ('rocks/rock_09', 96, 68, 0, 'Rocks/Pond West Shore Rock'),
        ('rocks/rock_10', 129, 84, 180, 'Rocks/Pond East Shore Spire'),
        ('rocks/rock_09', 30, 30, 90, 'Rocks/NW Corner Outcrop'),
        ('rocks/rock_07', 122, 28, 180, 'Rocks/NE Corner Outcrop'),
        ('rocks/rock_09', 28, 122, 270, 'Rocks/SW Corner Outcrop'),
        ('rocks/rock_10', 124, 122, 0, 'Rocks/SE Corner Outcrop'),
    ]
    for rid, rx_, rz_, rot, pname in rock_assets:
        c.stamp(rid, rx_, rz_, rotate=rot, sink=1, ground_fill='stone', part_name=pname)

    # Scatter 34 small mossy rocks & boulders along shores, corners, hills, and trail bends
    small_rock_coords = [
        (10, 12), (27, 9), (9, 27), (40, 29),
        (140, 11), (122, 9), (141, 28), (118, 36),
        (10, 140), (28, 141), (9, 122), (48, 138),
        (140, 140), (123, 141), (141, 122), (138, 102),
        (97, 83), (103, 62), (123, 63), (126, 88), (108, 92), (119, 93),
        (60, 48), (90, 48), (60, 96), (90, 96),
        (14, 58), (14, 86), (36, 60), (36, 90),
        (64, 140), (88, 140), (58, 16), (92, 14),
    ]
    for idx, (bx, bz) in enumerate(small_rock_coords):
        rad = 1.4 + (idx % 4) * 0.28
        terrain.place_boulder(c, bx, bz, radius=rad, mossy=(idx % 3 != 0), part_name='Rocks/Small Mossy Rocks', seed=1000 + idx)

    # ------------------------------------------------------------ 9. Lantern Avenues, Scenic Benches & Meadow Flora
    lamp_coords = [
        # Central Plaza & 4 Cardinal Avenues
        (71, 60), (79, 60), (71, 48), (79, 48), (71, 36), (79, 36),
        (71, 90), (79, 90), (71, 102), (79, 102), (71, 114), (79, 114),
        (90, 72), (90, 80), (96, 72), (96, 80),
        (60, 71), (60, 79), (51, 71), (51, 79), (41, 71), (41, 79),
        # Lake Shore & Overlook Loop
        (102, 60), (113, 57), (124, 61), (133, 71), (133, 81),
        (102, 91), (113, 94), (124, 91), (104, 46), (114, 46),
        # Village, Market, Camp & Homestead
        (45, 55), (52, 55), (45, 92), (52, 92), (35, 48), (35, 76),
        (34, 112), (44, 124), (60, 120), (92, 120), (112, 114),
        # Corner Sanctuary Lanterns
        (26, 26), (124, 26), (26, 124), (124, 124),
    ]
    for lx, lz in lamp_coords:
        if (lx, lz) not in pond['water_cells']:
            props.place_street_lamp(c, lx, lz, style='post', part_name='Props/Lantern Street Posts')

    bench_specs = [
        (96, 71, 'east'), (96, 81, 'east'),
        (108, 60, 'south'), (118, 60, 'south'),
        (108, 92, 'north'), (118, 92, 'north'),
        (68, 62, 'south'), (82, 62, 'south'),
        (68, 88, 'north'), (82, 88, 'north'),
        (48, 69, 'south'), (48, 81, 'north'),
        (105, 49, 'south'), (68, 122, 'south'),
    ]
    for bx, bz, fac in bench_specs:
        props.place_bench(c, x=bx, z=bz, facing=fac, length=3, part_name='Props/Scenic Benches')

    # Lush wildflowers, ferns, grass & berry bushes across all natural soil inside the border
    terrain.scatter_flora(
        c,
        bounds=(2, 2, 147, 147),
        density=0.26,
        excluded_cols=path_cols | pond['water_cells'],
        part_name='Nature/Wildflower Meadows',
        seed=1200,
    )

    # ------------------------------------------------------------ 10. Continuous Red Border Line Around Full 150x150 Build
    terrain.draw_border(
        c,
        block='red_concrete',
        width=1,
        raised=1,
        part_name='Border/Red Perimeter Line',
    )

    # Extra zoomed showcase cameras for close-up inspection alongside full 150x150 views
    c.add_camera('center-spawn', position=[54, 34, 98], target=[75, 16, 75], fov=50, lighting='golden')
    c.add_camera('fishing-pond', position=[131, 29, 98], target=[110, 12, 72], fov=52, lighting='day')
    c.add_camera('village-market', position=[64, 34, 96], target=[34, 15, 66], fov=50, lighting='golden')

    out_nbt = os.path.join(HERE, 'grand-haven-spawn.nbt')
    out_schem = os.path.join(HERE, 'grand-haven-spawn.schem')
    res = c.save(out_nbt, schem_path=out_schem)
    print('Saved %s & %s: %d blocks (%.1f KB)' % (res['nbt'], res['schem'], res['blocks'], res['bytes'] / 1024.0))
    return res


if __name__ == '__main__':
    build()
