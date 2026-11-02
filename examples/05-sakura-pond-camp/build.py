#!/usr/bin/env python3
"""Gold-standard 50x50 Spawn Example: Hanami Sanctuary (Sakura Pond & Shrine Camp).

Demonstrates the full design-first `mckit` pipeline:
  ZoneGrid -> sculpted island terrain -> watertight koi pond & waterfall ->
  curved paths -> hero pagoda, drum bridge, torii, pavilion, dock ->
  custom sakura/willow/pine/bamboo trees with working swings ->
  campfire camp, market stall, zen garden, lanterns & petal micro-detail.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'scripts')))

from mckit import Canvas, ZoneGrid, props, terrain, trees

ZONE_MAP = """
S H W G B
H H P P G
T P D P Z
C C R T M
C F O F M
"""

ZONE_LEGEND = {
    'H': 'Pagoda Shrine',
    'W': 'Waterfall Crag',
    'P': 'Koi Pond',
    'D': 'Drum Bridge',
    'G': 'Tea Pavilion',
    'B': 'Bamboo Grove',
    'Z': 'Zen Garden',
    'C': 'Campfire Camp',
    'T': 'Sakura Swing',
    'R': 'Torii Gate',
    'O': 'Spawn Pad',
    'M': 'Blossom Market',
    'S': 'Shrine Woods',
    'F': 'Petal Meadow',
}


def build():
    c = Canvas(50, 40, 50, theme='sakura')
    c.zones = ZoneGrid(50, 50, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

    # 1. Sculpt organic standalone island plot with NW shrine hill & walkable clearings
    terrain.sculpt_island_plot(
        c,
        base_y=9,
        hill_amp=2.2,
        mounds=[
            (13, 12, 11.5, 4.5),  # Hero NW outcrop for the 3-tier Pagoda Shrine
            (42, 8, 8.0, 2.2),    # Gentle NE rise behind bamboo grove
        ],
        flat_zones=[
            (13, 12, 5.5, 13),    # Pagoda plinth plateau
            (37, 12, 4.5, 10),    # Tea Pavilion terrace
            (13, 36, 6.2, 9),     # Campfire Camp clearing
            (26, 41, 4.5, 9),     # South Spawn & Torii approach
            (39, 38, 4.5, 9),     # Market Stall pocket
            (42, 24, 4.0, 9),     # Zen Rock Garden terrace
        ],
        edge_margin=1.8,
        underside=True,
        seed=2026,
    )

    # 2. Carve watertight Koi Pond in the heart of the sanctuary + stepping stones
    pond = terrain.carve_pond(
        c,
        center=(25, 22),
        rx=8.2,
        rz=6.8,
        depth=3,
        water_y=8,
        lily_density=0.11,
        reeds=True,
        stepping_stones=[(22, 18), (25, 17)],
        part_name='Water/Koi Pond',
        seed=108,
    )
    water_y = pond['water_y']

    # Craggy Waterfall pouring South-East from the Shrine hill (y=13) into the pond (y=8)!
    terrain.build_waterfall(
        c,
        cliff_x=19,
        cliff_z=16,
        top_y=13,
        water_y=water_y,
        dir_dx=1,
        dir_dz=1,
        part_name='Water/Shrine Waterfall',
        seed=209,
    )

    # Shoreline boulders framing the waterfall & pond banks
    terrain.place_boulder(c, 17, 17, radius=2.1, mossy=True, part_name='Nature/Waterfall Boulders', seed=11)
    terrain.place_boulder(c, 21, 14, radius=1.9, mossy=True, part_name='Nature/Waterfall Boulders', seed=12)
    terrain.place_boulder(c, 32, 26, radius=1.8, mossy=True, part_name='Nature/Pond Boulders', seed=13)
    terrain.place_boulder(c, 18, 28, radius=1.7, mossy=True, part_name='Nature/Pond Boulders', seed=14)

    # 3. Curved organic stone-brick & gravel pathways connecting every zone
    path_cols = set()
    # South Spawn -> Torii Gate -> Drum Bridge south abutment
    path_cols |= terrain.lay_path(c, [(26, 44), (26, 36), (25, 29)], width=2.2, part_name='Paths/Torii Avenue', seed=301)
    # North of Drum Bridge -> Shrine staircase & Tea Pavilion
    path_cols |= terrain.lay_path(c, [(25, 15), (21, 11), (18, 12)], width=2.0, part_name='Paths/Shrine Climb', seed=302)
    path_cols |= terrain.lay_path(c, [(25, 15), (31, 12), (34, 12)], width=1.9, part_name='Paths/Pavilion Walk', seed=303)
    # West branch: Torii -> Campfire Camp -> West Swing Tree -> Shrine steps
    path_cols |= terrain.lay_path(c, [(25, 36), (19, 37), (14, 36)], width=2.0, part_name='Paths/Camp Trail', seed=304)
    path_cols |= terrain.lay_path(c, [(12, 31), (9, 23), (13, 18)], width=1.8, part_name='Paths/West Ridge Path', seed=305)
    # East branch: Spawn -> Market Stall -> Zen Garden -> Pavilion
    path_cols |= terrain.lay_path(c, [(28, 41), (35, 40), (39, 34), (41, 27), (38, 16)], width=1.9, part_name='Paths/East Garden Loop', seed=306)

    # 4. Hero Landmark & Major Architecture
    # Hero 3-tier Pagoda Shrine on NW outcrop
    props.place_pagoda(c, cx=12, cz=11, tiers=3, base_half=4, part_name='Landmarks/Pagoda Shrine')

    # Iconic Vermilion Drum Bridge arching North-South across the Koi Pond!
    bridge_res = props.place_bridge(
        c,
        p_start=(25, 9, 29),
        p_end=(25, 9, 15),
        arch_height=3.2,
        half_width=1,
        part_name='Architecture/Vermilion Drum Bridge',
    )
    path_cols |= bridge_res['deck_cols']

    # Vermilion Torii Gate framing the bridge & pagoda from Spawn
    props.place_torii_gate(c, cx=26, cz=35, axis='x', half_span=3, height=7, part_name='Landmarks/Torii Gate')

    # NE Tea Pavilion overlooking the pond
    props.place_gazebo(c, cx=37, cz=11, radius=3, part_name='Architecture/Tea Pavilion')

    # Wooden Pond Fishing Dock jutting from the East shore
    props.place_dock(c, start_xz=(33, 21), dir_dx=-1, dir_dz=0, length=5, half_width=1, water_y=water_y, part_name='Architecture/Koi Pier')

    # East Zen Raked-Gravel Rock Garden
    props.place_zen_garden(c, cx=42, cz=24, rx=3, rz=3, part_name='Zones/Zen Rock Garden', seed=606)

    # 5. Campfire Camp, Blossom Market & Spawn Medallion
    camp_res = props.place_campfire_camp(c, cx=13, cz=37, radius=5.2, tents=2, part_name='Zones/Campfire Camp', seed=505)
    path_cols |= camp_res.get('occupied', set())

    props.place_market_stall(c, cx=39, cz=40, facing='north', part_name='Zones/Blossom Market Stall')
    props.place_market_stall(c, cx=43, cz=35, facing='west', color_pair=('white_wool', 'pink_wool'), part_name='Zones/Tea Sweet Stall')

    # Spawn Medallion at South entrance facing the Torii Gate, Bridge & Pagoda Shrine
    props.place_spawn_pad(c, cx=26, cz=43, radius=2, look_at=(16, 14, 14), part_name='Zones/Spawn Pad')

    # 6. Custom Organic Trees, Tree Swings & Bamboo Grove
    # West Giant Sakura with hanging Swing overlooking pond & camp!
    t_west = trees.place_tree(
        c, x=8, z=25, species='sakura', scale=1.08, with_swing_branch=True,
        hang_lanterns=2, part_name='Nature/Sakura Tree West', seed=701,
    )
    if t_west['swing']:
        props.place_swing(c, t_west['swing'], part_name='Props/West Sakura Swing')

    # South-East Giant Sakura with second Swing! (positioned on East bank so Torii -> Bridge sightline stays wide open)
    t_se = trees.place_tree(
        c, x=36, z=30, species='sakura', scale=1.00, with_swing_branch=True,
        hang_lanterns=2, part_name='Nature/Sakura Tree South-East', seed=702,
    )
    if t_se['swing']:
        props.place_swing(c, t_se['swing'], part_name='Props/East Sakura Swing')

    # Shrine backdrop Sakura on the NW ridge
    trees.place_tree(c, x=5, z=6, species='sakura', scale=0.92, hang_lanterns=2, part_name='Nature/Shrine Ridge Sakura', seed=703)
    # South-West corner Sakura & boulder overlook behind the campsite (cell [0,4])
    trees.place_tree(c, x=6, z=43, species='sakura', scale=0.90, hang_lanterns=2, part_name='Nature/Camp Corner Sakura', seed=712)
    terrain.place_boulder(c, 4, 41, radius=1.9, mossy=True, part_name='Nature/Camp Corner Boulders', seed=713)
    # South framing Sakura trees set wide so Spawn -> Torii -> Drum Bridge -> Pagoda sightline is unobstructed
    trees.place_tree(c, x=17, z=45, species='sakura', scale=0.80, hang_lanterns=1, part_name='Nature/Entrance Sakura West', seed=704)
    trees.place_tree(c, x=35, z=45, species='sakura', scale=0.80, hang_lanterns=1, part_name='Nature/Entrance Sakura East', seed=705)
    # Weeping Willow dipping gracefully over the North-East pond bank
    trees.place_tree(c, x=31, z=15, species='weeping_willow', scale=0.92, hang_lanterns=2, part_name='Nature/Pond Weeping Willow', seed=706)
    # Windswept Bonsai Japanese Pine beside the waterfall & Zen garden
    trees.place_tree(c, x=24, z=7, species='japanese_pine', scale=0.92, hang_lanterns=1, part_name='Nature/Waterfall Bonsai Pine', seed=707)
    trees.place_tree(c, x=44, z=17, species='japanese_pine', scale=0.85, hang_lanterns=1, part_name='Nature/Zen Bonsai Pine', seed=708)
    # Flowering Azalea accent tree near camp ridge
    trees.place_tree(c, x=5, z=16, species='azalea', scale=0.95, hang_lanterns=1, part_name='Nature/Ridge Azalea', seed=709)

    # Dense Bamboo Sanctuary in the NE corner (`cx=4, cz=0`)
    trees.place_bamboo_clump(c, x=44, z=7, radius=3.4, stalks=14, part_name='Nature/NE Bamboo Grove', seed=710)
    terrain.place_boulder(c, 45, 5, radius=1.7, mossy=True, part_name='Nature/NE Bamboo Grove', seed=711)

    # 7. Tōrō Stone Lanterns, Scenic Benches & Petal Meadow Micro-Detail
    lantern_spots = [
        (22, 39), (30, 39),  # Flanking Spawn -> Torii avenue
        (22, 31), (29, 31),  # South pond bank
        (21, 13), (33, 13),  # North shrine & pavilion walk
        (16, 32), (36, 37),  # Camp & market entries
        (42, 10), (8, 33),   # Bamboo grove & camp west
    ]
    for idx, (lx, lz) in enumerate(lantern_spots):
        props.place_street_lamp(c, lx, lz, style='toro', part_name=f'Props/Toro Lanterns')

    props.place_bench(c, x=20, z=31, facing='north', length=3, part_name='Props/Pond Overlook Bench')
    props.place_bench(c, x=35, z=28, facing='west', length=3, part_name='Props/East Shore Bench')
    props.place_bench(c, x=30, z=43, facing='north', length=3, part_name='Props/Spawn Welcome Bench')

    # Rich meadow flora & fallen cherry blossom petals across all natural ground
    terrain.scatter_flora(
        c,
        density=0.28,
        excluded_cols=path_cols,
        part_name='Nature/Blossom Meadow Flora',
        seed=909,
    )

    out_nbt = os.path.join(HERE, 'sakura-pond-camp.nbt')
    res = c.save(out_nbt)
    print('Saved %s: %d blocks (%.1f KB)' % (res['nbt'], res['blocks'], res['bytes'] / 1024.0))
    return res


if __name__ == '__main__':
    build()
