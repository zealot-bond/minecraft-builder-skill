#!/usr/bin/env python3
"""Gold-standard 32x32 Spawn Example: Aether Core (Neon Solarpunk Plaza).

Demonstrates theme generality: same `mckit` primitives + `futuristic` theme card
produce a sleek sci-fi / solarpunk hub with a Holo Energy Spire, glowing moat,
holo-rotunda, bioluminescent trees, neon pylons, and supply kiosks.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'scripts')))

from mckit import Canvas, ZoneGrid, props, terrain, trees

ZONE_MAP = """
P H H B
T S S N
W S S E
K O O M
"""

ZONE_LEGEND = {
    'P': 'Holo Pavilion',
    'H': 'North Terrace',
    'B': 'Bio Garden',
    'T': 'Neon Swing Tree',
    'S': 'Holo Spire',
    'N': 'East Bio Tree',
    'W': 'West Concourse',
    'E': 'East Concourse',
    'K': 'Supply Kiosk',
    'O': 'Spawn Gate',
    'M': 'Tech Stall',
}


def build():
    c = Canvas(32, 34, 32, theme='futuristic')
    c.zones = ZoneGrid(32, 32, ascii_map=ZONE_MAP, legend=ZONE_LEGEND)

    # 1. Sculpt sleek terraced sci-fi island with raised north deck & underside strata
    terrain.sculpt_island_plot(
        c,
        base_y=8,
        hill_amp=1.9,
        mounds=[
            (7, 7, 7.5, 3.0),     # NW elevated deck for Holo Pavilion
            (25, 7, 7.0, 2.5),    # NE elevated bio-garden terrace
        ],
        flat_zones=[
            (16, 15, 6.5, 8),     # Central Holo Spire plaza
            (16, 26, 4.5, 8),     # South Spawn & Gate pad
            (7, 7, 3.8, 11),      # NW Pavilion terrace
        ],
        edge_margin=1.4,
        underside=True,
        seed=3099,
    )

    # Lush moss/bio-soil pockets in the garden quadrants so flora thrives
    with c.part('Terrain/Bio Pockets'):
        for cx_, cz_, r in ((6, 18, 4.2), (25, 17, 4.2), (24, 7, 4.0), (16, 5, 3.5)):
            for dz in range(-5, 6):
                for dx in range(-5, 6):
                    if dx * dx + dz * dz <= r * r:
                        px, pz = cx_ + dx, cz_ + dz
                        gy = c.ground_y(px, pz)
                        if gy >= 2:
                            c.set(px, gy, pz, 'moss_block' if (dx + dz) % 2 == 0 else 'cyan_terracotta')

    # 2. Curved Smooth-Quartz Concourse Paths
    path_cols = set()
    path_cols |= terrain.lay_path(c, [(16, 28), (16, 21)], width=2.2, part_name='Paths/South Axis', seed=41)
    path_cols |= terrain.lay_path(c, [(16, 24), (8, 22), (7, 13)], width=1.8, part_name='Paths/West Loop', seed=42)
    path_cols |= terrain.lay_path(c, [(16, 24), (24, 22), (25, 12)], width=1.8, part_name='Paths/East Loop', seed=43)
    path_cols |= terrain.lay_path(c, [(9, 9), (16, 7), (23, 8)], width=1.8, part_name='Paths/North Skywalk', seed=44)

    # 3. Hero Holo Energy Spire & Architecture
    props.place_holo_spire(c, cx=16, cz=15, radius=5, height=18, part_name='Landmarks/Holo Energy Spire')
    props.place_gazebo(c, cx=7, cz=7, radius=3, part_name='Architecture/NW Holo Pavilion')
    props.place_torii_gate(c, cx=16, cz=22, axis='x', half_span=3, height=7, part_name='Landmarks/Energy Entry Arch')

    # Tech Kiosks & Spawn Pad
    props.place_market_stall(c, cx=7, cz=26, facing='east', part_name='Zones/Supply Kiosk West')
    props.place_market_stall(c, cx=25, cz=26, facing='west', color_pair=('light_blue_wool', 'white_wool'), part_name='Zones/Tech Stall East')
    props.place_spawn_pad(c, cx=16, cz=28, radius=2, look_at=(16, 12, 15), part_name='Zones/Spawn Pad')

    # 4. Bioluminescent Neon Trees & Swing
    tw = trees.place_tree(
        c, x=5, z=17, species='neon_tree', scale=0.95, with_swing_branch=True,
        hang_lanterns=2, part_name='Nature/West Bio Tree', seed=801,
    )
    if tw['swing']:
        props.place_swing(c, tw['swing'], part_name='Props/Holo Swing')

    trees.place_tree(c, x=26, z=16, species='neon_tree', scale=0.95, hang_lanterns=2, part_name='Nature/East Bio Tree', seed=802)
    trees.place_tree(c, x=25, z=6, species='neon_tree', scale=0.90, hang_lanterns=2, part_name='Nature/NE Bio Tree', seed=803)
    trees.place_tree(c, x=15, z=5, species='azalea', scale=0.88, hang_lanterns=1, part_name='Nature/North Azalea', seed=804)

    # Crystalline boulders
    terrain.place_boulder(c, 22, 9, radius=1.7, palette=['amethyst_block', 'calcite', 'deepslate_tiles'], mossy=False, part_name='Nature/Crystal Pods', seed=810)
    terrain.place_boulder(c, 10, 22, radius=1.5, palette=['amethyst_block', 'calcite', 'polished_deepslate'], mossy=False, part_name='Nature/Crystal Pods', seed=811)

    # 5. Neon Street Pylons, Benches & Bioluminescent Flora
    for lx, lz in [(12, 25), (20, 25), (10, 14), (22, 14), (12, 8), (20, 8), (6, 22), (26, 22)]:
        props.place_street_lamp(c, lx, lz, style='neon', part_name='Props/Neon Pylons')

    props.place_bench(c, x=9, z=20, facing='east', length=3, part_name='Props/West Plaza Bench')
    props.place_bench(c, x=23, z=20, facing='west', length=3, part_name='Props/East Plaza Bench')

    terrain.scatter_flora(
        c,
        density=0.30,
        excluded_cols=path_cols,
        part_name='Nature/Bioluminescent Flora',
        seed=820,
    )

    out_nbt = os.path.join(HERE, 'neon-futuristic-plaza.nbt')
    res = c.save(out_nbt)
    print('Saved %s: %d blocks (%.1f KB)' % (res['nbt'], res['blocks'], res['bytes'] / 1024.0))
    return res


if __name__ == '__main__':
    build()
