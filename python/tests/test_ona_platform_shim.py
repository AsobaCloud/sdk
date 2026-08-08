"""Deprecation shim for the renamed asoba package."""

from __future__ import annotations

import pytest


def test_ona_platform_shim_emits_deprecation_and_exposes_client():
    with pytest.warns(DeprecationWarning, match="renamed to 'asoba'"):
        import ona_platform

    assert hasattr(ona_platform, "OnaClient")
    from asoba import OnaClient

    assert ona_platform.OnaClient is OnaClient
