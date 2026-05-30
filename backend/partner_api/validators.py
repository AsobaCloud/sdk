"""
Input validation for the Partner API.
"""
import re

SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_ -]+$')

class ValidationError(Exception):
    """Raised when input parameters fail validation."""

def _validate_safe_id(value: str, field_name: str) -> None:
    """Validate that a string matches SAFE_ID_PATTERN."""
    if not SAFE_ID_PATTERN.match(value):
        raise ValidationError(
            f"'{field_name}' contains invalid characters. "
            f"Only alphanumeric characters, hyphens, and underscores are allowed."
        )

def validate_partner_params(params: dict, path: str) -> dict:
    """
    Validate query parameters for Partner API endpoints.
    """
    site_id = params.get("site_id")
    if not site_id:
        raise ValidationError("Missing required parameter: 'site_id'")
    
    _validate_safe_id(site_id, "site_id")
    
    kind = None
    if path == "/snapshot":
        kind = params.get("kind")
        if not kind:
            raise ValidationError("Missing required parameter: 'kind'")
        _validate_safe_id(kind, "kind")
    
    return {
        "site_id": site_id,
        "kind": kind
    }
