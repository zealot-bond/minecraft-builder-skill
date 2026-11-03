"""Unit tests for the anti-emptiness quality gate (`scripts/quality.py`).

Verifies the core contract of v2:
1. An empty/flat plaza MUST FAIL `quality.py` even when structurally valid.
2. The flagship 150x150 production spawn (`06-grand-haven-150x150`) MUST PASS
   both `validate.py --strict` and `quality.py`, with an unbroken red border line.
"""

import os
import tempfile
import unittest

from tests.helpers import ROOT, run_quality, run_validate
from mckit import Canvas, load_schematic  # noqa: E402


class TestQualityGate(unittest.TestCase):
    def test_empty_flat_plaza_is_rejected_by_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = Canvas(48, 8, 48, theme='vanilla_plus')
            with c.part('Terrain/FlatSlab'):
                c.fill(0, 0, 0, 47, 1, 47, 'stone_bricks')
            flat_nbt = os.path.join(tmp, 'flat-plaza.nbt')
            c.save(flat_nbt)

            rc_v, out_v = run_validate(flat_nbt)
            self.assertEqual(rc_v, 0, out_v)

            rc_q, out_q = run_quality(flat_nbt, extra_args=['--heatmap', os.path.join(tmp, 'hm.png')])
            self.assertNotEqual(rc_q, 0, f'Expected empty flat plaza to FAIL quality gate, got PASS:\n{out_q}')
            self.assertIn('QUALITY GATE FAILED', out_q)

    def test_grand_haven_150x150_passes_both_gates_and_has_red_border(self):
        nbt_path = os.path.join(ROOT, 'examples', '06-grand-haven-150x150', 'grand-haven-spawn.nbt')
        schem_path = os.path.join(ROOT, 'examples', '06-grand-haven-150x150', 'grand-haven-spawn.schem')
        self.assertTrue(os.path.exists(nbt_path), f'Missing {nbt_path}')
        self.assertTrue(os.path.exists(schem_path), f'Missing {schem_path}')

        rc_v, out_v = run_validate(nbt_path)
        self.assertEqual(rc_v, 0, out_v)

        with tempfile.TemporaryDirectory() as tmp:
            rc_q, out_q = run_quality(nbt_path, extra_args=['--heatmap', os.path.join(tmp, 'hm.png')])
            self.assertEqual(rc_q, 0, out_q)

        # Verify continuous red border line on all 4 perimeter edges (x=0, x=149, z=0, z=149)
        asset = load_schematic(nbt_path)
        self.assertEqual((asset.sx, asset.sz), (150, 150))
        red_cols = set()
        for x, y, z, b, _ in asset.iter_blocks():
            if b == 'red_concrete' and (x in (0, 149) or z in (0, 149)):
                red_cols.add((x, z))
        expected_perimeter = 150 * 4 - 4
        self.assertEqual(len(red_cols), expected_perimeter)

    def test_skyhaven_100x100_box_in_box_pvp_passes_gates_and_borders(self):
        nbt_path = os.path.join(ROOT, 'examples', '07-skyhaven-pvp-100x100', 'skyhaven-pvp-spawn.nbt')
        schem_path = os.path.join(ROOT, 'examples', '07-skyhaven-pvp-100x100', 'skyhaven-pvp-spawn.schem')
        self.assertTrue(os.path.exists(nbt_path), f'Missing {nbt_path}')
        self.assertTrue(os.path.exists(schem_path), f'Missing {schem_path}')

        rc_v, out_v = run_validate(nbt_path)
        self.assertEqual(rc_v, 0, out_v)

        with tempfile.TemporaryDirectory() as tmp:
            rc_q, out_q = run_quality(nbt_path, extra_args=['--heatmap', os.path.join(tmp, 'hm.png')])
            self.assertEqual(rc_q, 0, out_q)

        asset = load_schematic(nbt_path)
        self.assertEqual((asset.sx, asset.sz), (100, 100))
        red_inner = set()
        blue_outer = set()
        glass_outer = set()
        for x, y, z, b, _ in asset.iter_blocks():
            if b == 'red_concrete' and ((x in (25, 74) and 25 <= z <= 74) or (z in (25, 74) and 25 <= x <= 74)):
                red_inner.add((x, z))
            if x in (0, 99) or z in (0, 99):
                if b == 'blue_concrete':
                    blue_outer.add((x, z))
                elif b == 'blue_stained_glass':
                    glass_outer.add((x, z))
        self.assertEqual(len(red_inner), 50 * 4 - 4)
        self.assertEqual(len(blue_outer), 100 * 4 - 4)
        self.assertGreaterEqual(len(glass_outer), 350)


if __name__ == '__main__':
    unittest.main()
