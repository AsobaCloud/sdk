"""Cursor serialization for inverter telemetry streaming."""

import base64
import json

from ..exceptions import ValidationError
from ..models.telemetry import CursorObject


class CursorSerializer:
    @staticmethod
    def serialize(asset_id: str, timestamp: str) -> str:
        payload = json.dumps({"asset_id": asset_id, "timestamp": timestamp})
        return base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()

    @staticmethod
    def deserialize(cursor: str) -> CursorObject:
        try:
            padded = cursor + "=" * (4 - len(cursor) % 4) if len(cursor) % 4 else cursor
            data = json.loads(base64.urlsafe_b64decode(padded).decode())
        except Exception as e:
            raise ValidationError(f"Cursor is malformed: {e}") from e
        if not isinstance(data, dict):
            raise ValidationError("Cursor must decode to a JSON object")
        for field in ("asset_id", "timestamp"):
            if field not in data:
                raise ValidationError(f"Cursor missing required field: '{field}'")
            if not isinstance(data[field], str):
                raise ValidationError(f"Cursor field '{field}' must be a string")
        return CursorObject(asset_id=data["asset_id"], timestamp=data["timestamp"])
