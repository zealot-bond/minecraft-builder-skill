"""Unit tests for `mckit.Canvas`, NBT round-trip, state dedup, auto-connect, and cleanup."""

import json
import os
import tempfile
import unittest

from tests.helpers import run_validate, validate
from mckit import Canvas, ZoneGrid


class TestCanvas(unittest.TestCase):
    def test_nbt_roundtrip_and_palette_dedup(self):
        c = Canvas(12, 10, 12, theme='sakura')
        c.zones = ZoneGrid(12, 12, ascii_map='A B\nC D', legend={'A': 'NW', 'B': 'NE', 'C': 'SW', 'D': 'SE'})
        with c.part('Floor'):
            c.fill_box(0, 0, 0, 11, 1, 11, 'stone_bricks')
            # Repeated identical blockstate calls should deduplicate to one palette entry
            c.set(2, 2, 2, 'cherry_leaves')
            c.set(3, 2, 2, 'cherry_leaves', persistent='true')
        c.set_spawn(6, 2, 6, look_at=(6, 4, 2))

        with tempfile.TemporaryDirectory() as tmp:
            nbt_path = os.path.join(tmp, 'test.nbt')
            info = c.save(nbt_path)
            self.assertTrue(os.path.exists(nbt_path))
            self.assertTrue(os.path.exists(info['manifest']))

            rc, out = run_validate(nbt_path)
            self.assertEqual(rc, 0, out)

            root, leftover = validate.load_nbt(nbt_path)
            self.assertEqual(leftover, 0)
            self.assertEqual(root['palette'][0]['Name'], 'minecraft:air')
            cherry_entries = [p for p in root['palette'] if p['Name'] == 'minecraft:cherry_leaves']
            self.assertEqual(len(cherry_entries), 1)
            self.assertEqual(cherry_entries[0]['Properties'].get('persistent'), 'true')

            with open(info['manifest'], 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            self.assertEqual(manifest['theme'], 'sakura')
            self.assertEqual(manifest['spawn']['pos'], [6, 2, 6])
            self.assertTrue(any(p['name'] == 'Floor' for p in manifest['parts']))

    def test_auto_connect_fences_walls_panes(self):
        c = Canvas(8, 6, 8, theme='vanilla_plus')
        c.fill_box(0, 0, 0, 7, 0, 7, 'stone')
        # L-shaped fence corner at (2, 1, 2) -> (3, 1, 2) and (2, 1, 3)
        c.set(2, 1, 2, 'oak_fence')
        c.set(3, 1, 2, 'oak_fence')
        c.set(2, 1, 3, 'oak_fence')

        # Wall between two solid neighbors along Z
        c.set(5, 1, 2, 'stone_bricks')
        c.set(5, 1, 3, 'stone_brick_wall')
        c.set(5, 1, 4, 'stone_bricks')

        c.auto_connect()
        _, corner_props = c.get_state(2, 1, 2)
        self.assertEqual(corner_props.get('east'), 'true')
        self.assertEqual(corner_props.get('south'), 'true')
        self.assertEqual(corner_props.get('north'), 'false')
        self.assertEqual(corner_props.get('west'), 'false')

        _, wall_props = c.get_state(5, 1, 3)
        self.assertEqual(wall_props.get('north'), 'low')
        self.assertEqual(wall_props.get('south'), 'low')

    def test_clean_floating_foliage_and_plants(self):
        c = Canvas(10, 12, 10, theme='sakura')
        c.fill_box(0, 0, 0, 9, 1, 9, 'grass_block')
        # Grounded mini-trunk + leaf
        c.set(3, 2, 3, 'cherry_wood')
        c.set(3, 3, 3, 'cherry_leaves')
        # Stray floating leaf cluster high in air + floating flower
        c.set(7, 8, 7, 'cherry_leaves')
        c.set(7, 8, 8, 'cherry_leaves')
        c.set(5, 6, 5, 'dandelion')

        with tempfile.TemporaryDirectory() as tmp:
            nbt_path = os.path.join(tmp, 'clean.nbt')
            c.save(nbt_path)
            self.assertEqual(c.get(3, 3, 3), 'cherry_leaves')
            self.assertEqual(c.get(7, 8, 7), 'air')
            self.assertEqual(c.get(5, 6, 5), 'air')
            rc, out = run_validate(nbt_path)
            self.assertEqual(rc, 0, out)


if __name__ == '__main__':
    unittest.main()
