# coding: utf-8
import sys as _sys

PY_VERSION = _sys.version
PY2 = PY_VERSION < '3'

if PY2:
    from future.standard_library import print_function
    from future.builtins import str, int



