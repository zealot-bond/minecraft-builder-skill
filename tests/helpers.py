"""Shared test helpers for running `validate.py` and `quality.py` in-process."""

import contextlib
import io
import os
import sys
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS = os.path.join(ROOT, 'scripts')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import quality  # noqa: E402
import validate  # noqa: E402


def run_validate(nbt_path, extra_args=()):
    buf = io.StringIO()
    argv = ['validate.py', nbt_path, '--strict', *extra_args]
    with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(buf):
        rc = validate.main()
    return rc, buf.getvalue()


def run_quality(nbt_path, extra_args=()):
    buf = io.StringIO()
    argv = ['quality.py', nbt_path, *extra_args]
    with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(buf):
        rc = quality.main()
    return rc, buf.getvalue()
