"""Test package for the evals harness.

Ensures the harness modules (run.py, one directory up) are importable no matter
which runner or working directory is used, so individual test files can simply
`from run import ...`. This keeps every test file free of path boilerplate.

To add tests: drop a `test_<area>.py` file in this directory. It is picked up
automatically by `python3 -m unittest discover` (see evals/README.md) and by
pytest — no CI or config changes needed.
"""
import pathlib
import sys

_EVALS_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(_EVALS_DIR))
