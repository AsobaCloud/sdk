"""Backward-compatibility shim for the renamed ``asoba`` package.

``ona_platform`` has been renamed to ``asoba``. This module re-exports
``asoba`` and emits a :class:`DeprecationWarning` on import so existing
code keeps working during the migration window.
"""

from __future__ import annotations

import sys
import warnings

import asoba

warnings.warn(
    "'ona_platform' has been renamed to 'asoba'. "
    "Please update your imports to 'import asoba'. "
    "'ona_platform' will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

sys.modules[__name__] = asoba
