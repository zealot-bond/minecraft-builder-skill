"""Unit tests for Sponge `.schem` / `.nbt` asset library, rotation stamping, and examples."""

import os
import tempfile
import unittest

from mckit import Canvas, get_asset, load_catalog, load_schematic, terrain
from tests.helpers import ROOT, run_validate


class TestSchemAndAssetLibrary(unittest.TestCase):
    def test_catalog_and_imported_examples_present(self):
        cat = load_catalog()
        cats = cat.get('categories', {})
        self.assertGreaterEqual(cats.get('trees_oak', {}).get('count', 0), 60)
        self.assertGreaterEqual(cats.get('trees_assorted', {}).get('count', 0), 34)
        self.assertGreaterEqual(cats.get('houses', {}).get('count', 0), 260)
        self.assertGreaterEqual(cats.get('stalls', {}).get('count', 0), 5)
        self.assertGreaterEqual(cats.get('rocks', {}).get('count', 0), 10)

        for ex_dir in (
            '01-economy-smp-spawn',
            '02-japanese-spring-spawn',
            '03-survival-spawn',
            '04-red-kingdom-spawn',
            '05-trading-post',
            '06-grand-haven-150x150',
        ):
            p = os.path.join(ROOT, 'examples', ex_dir)
            self.assertTrue(os.path.isdir(p), f'Missing example folder: {p}')

    def test_stamp_rotated_asset_and_schem_roundtrip(self):
        c = Canvas(36, 36, 36, theme='vanilla_plus')
        terrain.sculpt_island_plot(c, base_y=6, hill_amp=1.0, full_plot=True, seed=9)
        stall = get_asset('stalls', 'stall_01')
        info = c.stamp(stall, x=18, z=18, rotate=90, part_name='Village/Stall01')
        self.assertGreater(info['placed'], 20)
        terrain.draw_border(c, block='red_concrete', width=1, raised=1)

        with tempfile.TemporaryDirectory() as tmp:
            nbt_path = os.path.join(tmp, 'test.nbt')
            schem_path = os.path.join(tmp, 'test.schem')
            c.save(nbt_path, schem_path=schem_path)
            rc_v, out_v = run_validate(nbt_path)
            self.assertEqual(rc_v, 0, out_v)

            reloaded = load_schematic(schem_path)
            self.assertEqual((reloaded.sx, reloaded.sy, reloaded.sz), (36, 36, 36))
            self.assertGreater(reloaded.count, 1000)


if __name__ == '__main__':
    unittest.main()
