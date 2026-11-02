"""Unit tests for sculpted terrain, watertight ponds, waterfalls, paths, and flora."""

import os
import tempfile
import unittest

from tests.helpers import run_validate
from mckit import Canvas, terrain


class TestTerrain(unittest.TestCase):
    def test_island_pond_and_waterfall_zero_leaks_across_seeds(self):
        for seed in (101, 555, 999):
            with self.subTest(seed=seed):
                c = Canvas(36, 30, 36, theme='sakura')
                terrain.sculpt_island_plot(
                    c,
                    base_y=8,
                    hill_amp=2.0,
                    mounds=[(10, 10, 8.0, 4.0)],
                    flat_zones=[(26, 26, 4.0, 8)],
                    underside=True,
                    seed=seed,
                )
                pond = terrain.carve_pond(
                    c,
                    center=(19, 19),
                    rx=6.5,
                    rz=5.5,
                    depth=3,
                    water_y=7,
                    lily_density=0.12,
                    reeds=True,
                    stepping_stones=[(18, 17)],
                    seed=seed + 10,
                )
                terrain.build_waterfall(
                    c,
                    cliff_x=14,
                    cliff_z=14,
                    top_y=12,
                    water_y=pond['water_y'],
                    dir_dx=1,
                    dir_dz=1,
                    seed=seed + 20,
                )
                path_cols = terrain.lay_path(c, [(28, 28), (24, 22), (18, 26)], width=2.0, seed=seed + 30)
                terrain.place_boulder(c, 12, 24, radius=1.8, mossy=True, seed=seed + 40)
                terrain.scatter_flora(c, density=0.22, excluded_cols=path_cols, seed=seed + 50)

                with tempfile.TemporaryDirectory() as tmp:
                    nbt_path = os.path.join(tmp, f'terrain_{seed}.nbt')
                    c.save(nbt_path)
                    rc, out = run_validate(nbt_path)
                    self.assertEqual(rc, 0, f'seed={seed} failed:\n{out}')
                    self.assertIn('fluid.containment      PASS', out)


if __name__ == '__main__':
    unittest.main()
