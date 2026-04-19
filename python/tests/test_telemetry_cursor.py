"""Property-based tests for CursorSerializer."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ona_platform.exceptions import ValidationError
from ona_platform.services.telemetry_cursor import CursorSerializer

_printable = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_:#"),
)


# Feature: inverter-telemetry-streaming, Property 1: Cursor round-trip
@given(
    asset_id=_printable,
    timestamp=st.just("2025-01-01T00:00:00"),
)
@settings(max_examples=200)
def test_property_1_cursor_round_trip(asset_id, timestamp):
    """Validates: Requirements 5.3, 5.4, 5.5"""
    cursor_str = CursorSerializer.serialize(asset_id, timestamp)
    result = CursorSerializer.deserialize(cursor_str)
    assert result.asset_id == asset_id
    assert result.timestamp == timestamp


# Feature: inverter-telemetry-streaming, Property 2: Malformed cursor always raises ValidationError
@given(
    st.one_of(
        # Random bytes that are not valid base64 JSON
        st.binary(min_size=1, max_size=50).map(lambda b: b.decode("latin-1")),
        # Random text that won't decode to a valid cursor
        st.text(min_size=1, max_size=50, alphabet="!@#$%^&*()"),
        # Valid base64 but not JSON object
        st.just("dGhpcyBpcyBub3QganNvbg"),  # "this is not json"
        # Empty string
        st.just(""),
    )
)
@settings(max_examples=200)
def test_property_2_malformed_cursor_raises_validation_error(bad_cursor):
    """Validates: Requirements 5.6"""
    with pytest.raises(ValidationError):
        CursorSerializer.deserialize(bad_cursor)
