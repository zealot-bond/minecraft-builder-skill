"""Unit tests for the anti-emptiness quality gate (`scripts/quality.py`).

Verifies the core contract of v2:
1. An empty/flat plaza (`examples/01-flat-plaza`) MUST FAIL `quality.py`.
2. Both rich spawns (`05-sakura-pond-camp` and `06-neon-futuristic-plaza`) MUST PASS
   both `validate.py --strict` and `quality.py`.
"""

import os
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import ROOT, SCRIPTS, run_quality, run_validate


class TestQualityGate(unittest.TestCase):
    def test_empty_flat_plaza_is_rejected_by_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            flat_script = os.path.join(ROOT, 'examples', '01-flat-plaza', 'build.py')
            with open(flat_script, 'r', encoding='utf-8') as f:
                src = f.read()
            tmp_script = os.path.join(tmp, 'build.py')
            with open(tmp_script, 'w', encoding='utf-8') as f:
                f.write(src)
            env = dict(os.environ, PYTHONPATH=SCRIPTS)
            subprocess.run([sys.executable, tmp_script], cwd=tmp, env=env, check=True, capture_output=True)
            flat_nbt = os.path.join(tmp, 'flat-plaza.nbt')
            self.assertTrue(os.path.exists(flat_nbt))

            # Flat plaza is structurally valid, EXCEPT quality gate MUST reject its emptiness!
            rc_q, out_q = run_quality(flat_nbt, extra_args=['--allow-no-manifest', '--heatmap', os.path.join(tmp, 'hm.png')])
            self.assertNotEqual(rc_q, 0, f'Expected empty flat plaza to FAIL quality gate, got PASS:\n{out_q}')
            self.assertIn('QUALITY GATE FAILED', out_q)

    def test_gold_standard_examples_pass_both_gates(self):
        examples = [
            os.path.join(ROOT, 'examples', '05-sakura-pond-camp', 'sakura-pond-camp.nbt'),
            os.path.join(ROOT, 'examples', '06-neon-futuristic-plaza', 'neon-futuristic-plaza.nbt'),
        ]
        for nbt_path in examples:
            with self.subTest(example=os.path.basename(nbt_path)):
                self.assertTrue(os.path.exists(nbt_path), f'Missing {nbt_path}')
                rc_v, out_v = run_validate(nbt_path)
                self.assertEqual(rc_v, 0, out_v)
                with tempfile.TemporaryDirectory() as tmp:
                    rc_q, out_q = run_quality(nbt_path, extra_args=['--heatmap', os.path.join(tmp, 'hm.png')])
                    self.assertEqual(rc_q, 0, out_q)


if __name__ == '__main__':
    unittest.main()
