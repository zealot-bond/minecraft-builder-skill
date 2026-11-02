"""Unit tests verifying every high-level architectural & organic prop passes `validate.py`."""

import os
import tempfile
import unittest

from tests.helpers import run_validate
from mckit import Canvas, props, terrain


class TestProps(unittest.TestCase):
    def _validate_canvas(self, c, label):
        with tempfile.TemporaryDirectory() as tmp:
            nbt_path = os.path.join(tmp, f'{label}.nbt')
            c.save(nbt_path)
            rc, out = run_validate(nbt_path)
            self.assertEqual(rc, 0, f'{label} failed:\n{out}')

    def test_pagoda_torii_gazebo_zen_garden(self):
        c = Canvas(40, 36, 40, theme='samurai')
        c.fill_box(0, 0, 0, 39, 5, 39, 'grass_block')
        props.place_pagoda(c, cx=12, cz=12, tiers=3, base_half=4)
        props.place_torii_gate(c, cx=12, cz=26, axis='x', half_span=3, height=7)
        props.place_gazebo(c, cx=29, cz=12, radius=3)
        props.place_zen_garden(c, cx=29, cz=28, rx=3, rz=3, seed=42)
        self._validate_canvas(c, 'landmarks_samurai')

    def test_holo_spire_and_futuristic_torii(self):
        c = Canvas(30, 32, 30, theme='futuristic')
        c.fill_box(0, 0, 0, 29, 6, 29, 'gray_concrete')
        props.place_holo_spire(c, cx=15, cz=13, radius=5, height=16)
        props.place_torii_gate(c, cx=15, cz=23, axis='x', half_span=3, height=7)
        props.place_street_lamp(c, 8, 22, style='neon')
        self._validate_canvas(c, 'holo_spire')

    def test_pond_bridge_dock_campfire_market_lamps_benches_spawn(self):
        c = Canvas(44, 28, 44, theme='vanilla_plus')
        c.fill_box(0, 0, 0, 43, 6, 43, 'grass_block')
        pond = terrain.carve_pond(c, center=(22, 16), rx=6.5, rz=5.5, depth=3, water_y=6, seed=12)
        props.place_bridge(c, p_start=(22, 7, 23), p_end=(22, 7, 9), arch_height=3.0, half_width=1)
        props.place_dock(c, start_xz=(29, 16), dir_dx=-1, dir_dz=0, length=4, half_width=1, water_y=pond['water_y'])
        props.place_campfire_camp(c, cx=11, cz=32, radius=5.0, tents=2, seed=99)
        props.place_market_stall(c, cx=33, cz=32, facing='north')
        props.place_street_lamp(c, 22, 28, style='post')
        props.place_street_lamp(c, 18, 28, style='toro')
        props.place_bench(c, x=26, z=28, facing='north', length=3)
        props.place_spawn_pad(c, cx=22, cz=37, radius=2, look_at=(22, 10, 16))
        self._validate_canvas(c, 'village_props')


if __name__ == '__main__':
    unittest.main()
