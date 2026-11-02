"""Unit tests for all 9 procedural tree species + bamboo clumps across seeds."""

import os
import tempfile
import unittest

from tests.helpers import run_validate
from mckit import Canvas, props, trees


class TestTrees(unittest.TestCase):
    def test_all_species_pass_strict_validation_across_seeds(self):
        for species in sorted(trees.SPECIES.keys()):
            for seed in (101, 202):
                with self.subTest(species=species, seed=seed):
                    c = Canvas(28, 32, 28, theme='sakura')
                    c.fill_box(0, 0, 0, 27, 2, 27, 'grass_block')
                    info = trees.place_tree(
                        c,
                        x=14,
                        z=14,
                        species=species,
                        scale=1.0,
                        with_swing_branch=(seed == 101),
                        hang_lanterns=2,
                        seed=seed,
                    )
                    self.assertGreater(info.get('blocks', 0), 50)
                    if seed == 101 and info.get('swing'):
                        props.place_swing(c, info['swing'])

                    with tempfile.TemporaryDirectory() as tmp:
                        nbt_path = os.path.join(tmp, f'{species}_{seed}.nbt')
                        c.save(nbt_path)
                        rc, out = run_validate(nbt_path)
                        self.assertEqual(rc, 0, f'{species} seed={seed} failed:\n{out}')

    def test_bamboo_clump_validates(self):
        c = Canvas(16, 20, 16, theme='samurai')
        c.fill_box(0, 0, 0, 15, 2, 15, 'podzol')
        trees.place_bamboo_clump(c, x=8, z=8, radius=3.0, stalks=9, seed=77)
        with tempfile.TemporaryDirectory() as tmp:
            nbt_path = os.path.join(tmp, 'bamboo.nbt')
            c.save(nbt_path)
            rc, out = run_validate(nbt_path)
            self.assertEqual(rc, 0, out)


if __name__ == '__main__':
    unittest.main()
