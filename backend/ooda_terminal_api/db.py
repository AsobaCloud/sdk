"""
DynamoDB query logic for the OODA Terminal API.

Queries the appropriate table and GSI based on resolution, strips internal
fields, converts Decimal types to float, and returns alerts sorted by
timestamp ascending.

Requirements: 1.1–1.5, 2.1–2.2, 6.2
"""
import base64
import json
import logging
from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Table / index configuration
# ---------------------------------------------------------------------------

_AWS_REGION = "af-south-1"
_TABLE_5MIN = "ona-platform-ooda-5min"
_TABLE_DAILY = "ona-platform-ooda-daily"

# Fields that must never appear in API responses (Req 6.2)
_STRIP_FIELDS = {"expires_at", "terminal_ts"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_table(table_name: str):
    """Return a boto3 DynamoDB Table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=_AWS_REGION)
    return dynamodb.Table(table_name)


def _convert_decimals(obj):
    """Recursively convert Decimal values to float in a dict/list structure."""
    if isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def _strip_internal_fields(alert: dict) -> dict:
    """Remove internal DynamoDB fields that must not be exposed to callers."""
    return {k: v for k, v in alert.items() if k not in _STRIP_FIELDS}


def _decode_cursor(cursor: str) -> dict:
    """
    Deserialize a base64url JSON cursor string into a dict suitable for use
    as ExclusiveStartKey in a DynamoDB Query call.
    """
    padded = cursor + "=" * (4 - len(cursor) % 4) if len(cursor) % 4 else cursor
    decoded = base64.urlsafe_b64decode(padded)
    return json.loads(decoded.decode("utf-8"))


def _encode_cursor(terminal_device_id: str, timestamp: str) -> str:
    """
    Encode terminal_device_id and timestamp as a URL-safe base64 cursor.
    """
    cursor_data = {
        "terminal_device_id": terminal_device_id,
        "timestamp": timestamp
    }
    cursor_json = json.dumps(cursor_data, separators=(',', ':'))
    cursor_bytes = cursor_json.encode('utf-8')
    return base64.urlsafe_b64encode(cursor_bytes).decode('ascii').rstrip('=')


# ---------------------------------------------------------------------------
# Public query functions
# ---------------------------------------------------------------------------

def query_terminal_alerts(
    terminal_device_id: str,
    site_id: str,
    start: str,
    end: str,
    resolution: str,
    limit: int,
    cursor: Optional[str] = None,
) -> list:
    """
    Query OODA alerts for a single terminal device.

    For resolution "5min": queries the TerminalTimeIndex GSI on
    ona-platform-ooda-5min using terminal_device_id + timestamp range.

    For resolution "daily": queries the TerminalDateIndex GSI on
    ona-platform-ooda-daily using terminal_device_id + date range.

    Returns alerts sorted by timestamp ascending with internal fields stripped
    and Decimal values converted to float. Each alert includes a cursor field.
    """
    if resolution == "5min":
        table = _get_table(_TABLE_5MIN)
        key_condition = (
            Key("terminal_device_id").eq(terminal_device_id)
            & Key("timestamp").between(start, end)
        )
        index_name = "TerminalTimeIndex"
    else:  # "daily"
        table = _get_table(_TABLE_DAILY)
        key_condition = (
            Key("terminal_device_id").eq(terminal_device_id)
            & Key("date").between(start, end)
        )
        index_name = "TerminalDateIndex"

    query_kwargs = {
        "IndexName": index_name,
        "KeyConditionExpression": key_condition,
        "Limit": limit,
        "ScanIndexForward": True,  # ascending order
    }

    if cursor:
        query_kwargs["ExclusiveStartKey"] = _decode_cursor(cursor)

    try:
        response = table.query(**query_kwargs)
    except Exception as exc:
        logger.error("DynamoDB query failed for terminal_device_id=%s: %s", terminal_device_id, exc)
        raise

    items = response.get("Items", [])
    cleaned = []
    for item in items:
        alert = _strip_internal_fields(item)
        # Add cursor field to each alert
        alert["cursor"] = _encode_cursor(
            item["terminal_device_id"], 
            item["timestamp"] if resolution == "5min" else item["date"]
        )
        cleaned.append(alert)
    
    return _convert_decimals(cleaned)


def query_site_alerts(
    site_id: str,
    start: str,
    end: str,
    resolution: str,
    limit: int,
) -> dict:
    """
    Query OODA alerts for all terminal devices at a site.

    For resolution "5min": queries the primary key on ona-platform-ooda-5min
    using site_id + terminal_ts BETWEEN "{site_id}#{start}" AND "{site_id}#{end}".

    For resolution "daily": queries the primary key on ona-platform-ooda-daily
    using site_id + terminal_date BETWEEN "{site_id}#{start}" AND "{site_id}#{end}".

    Returns a dict mapping terminal_device_id -> list of alerts sorted by timestamp ascending.
    Internal fields (expires_at) are stripped; Decimal values are converted to float.
    Each alert includes a cursor field.
    """
    if resolution == "5min":
        table = _get_table(_TABLE_5MIN)
        # Query by site_id (PK) with timestamp filter — terminal_ts is terminal_device_id#timestamp
        # so we can't use it for range filtering by time directly
        key_condition = Key("site_id").eq(site_id)
        query_kwargs = {
            "KeyConditionExpression": key_condition,
            "FilterExpression": "#ts BETWEEN :start AND :end",
            "ExpressionAttributeNames": {"#ts": "timestamp"},
            "ExpressionAttributeValues": {":start": start, ":end": end},
            "Limit": limit,
            "ScanIndexForward": True,
        }
    else:  # "daily"
        table = _get_table(_TABLE_DAILY)
        sk_start = f"{site_id}#{start}"
        sk_end = f"{site_id}#{end}"
        key_condition = (
            Key("site_id").eq(site_id)
            & Key("terminal_date").between(sk_start, sk_end)
        )
        query_kwargs = {
            "KeyConditionExpression": key_condition,
            "Limit": limit,
            "ScanIndexForward": True,
        }

    try:
        response = table.query(**query_kwargs)
    except Exception as exc:
        logger.error("DynamoDB site query failed for site_id=%s: %s", site_id, exc)
        raise

    items = response.get("Items", [])

    # Group by terminal_device_id
    result: dict = {}
    for item in items:
        terminal_device_id = item.get("terminal_device_id", "")
        alert = _strip_internal_fields(item)
        # Add cursor field to each alert
        alert["cursor"] = _encode_cursor(
            item["terminal_device_id"], 
            item["timestamp"] if resolution == "5min" else item["date"]
        )
        converted = _convert_decimals(alert)
        result.setdefault(terminal_device_id, []).append(converted)

    # Each group is already in ascending order (ScanIndexForward=True)
    return result


def get_data_period(site_id: str, terminal_device_id: str = None) -> dict:
    """
    Return the earliest and latest timestamp for a site or specific terminal device.
    Queries ona-platform-ooda-5min using the appropriate index.
    """
    if terminal_device_id:
        # Query TerminalTimeIndex GSI — get first and last alert for this terminal device
        table = _get_table(_TABLE_5MIN)

        # Get earliest
        first_resp = table.query(
            IndexName="TerminalTimeIndex",
            KeyConditionExpression=Key("terminal_device_id").eq(terminal_device_id),
            ScanIndexForward=True,
            Limit=1,
        )
        # Get latest
        last_resp = table.query(
            IndexName="TerminalTimeIndex",
            KeyConditionExpression=Key("terminal_device_id").eq(terminal_device_id),
            ScanIndexForward=False,
            Limit=1,
        )
        first_items = first_resp.get("Items", [])
        last_items = last_resp.get("Items", [])
        return {
            "site_id": site_id,
            "terminal_device_id": terminal_device_id,
            "first_record": first_items[0]["timestamp"] if first_items else None,
            "last_record": last_items[0]["timestamp"] if last_items else None,
        }
    else:
        # Query by site_id primary key — get first and last alert for the site
        table = _get_table(_TABLE_5MIN)

        first_resp = table.query(
            KeyConditionExpression=Key("site_id").eq(site_id),
            ScanIndexForward=True,
            Limit=1,
        )
        last_resp = table.query(
            KeyConditionExpression=Key("site_id").eq(site_id),
            ScanIndexForward=False,
            Limit=1,
        )
        first_items = first_resp.get("Items", [])
        last_items = last_resp.get("Items", [])
        return {
            "site_id": site_id,
            "first_record": first_items[0]["timestamp"] if first_items else None,
            "last_record": last_items[0]["timestamp"] if last_items else None,
        }