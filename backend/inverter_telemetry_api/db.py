"""
DynamoDB query logic for the Inverter Telemetry API.

Queries the appropriate table and GSI based on resolution, strips internal
fields, converts Decimal types to float, and returns records sorted by
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
_TABLE_5MIN = "ona-platform-telemetry-5min"
_TABLE_DAILY = "ona-platform-telemetry-daily"

# Fields that must never appear in API responses (Req 6.2)
_STRIP_FIELDS = {"expires_at", "asset_ts"}


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


def _strip_internal_fields(record: dict) -> dict:
    """Remove internal DynamoDB fields that must not be exposed to callers."""
    return {k: v for k, v in record.items() if k not in _STRIP_FIELDS}


def _decode_cursor(cursor: str) -> dict:
    """
    Deserialize a base64url JSON cursor string into a dict suitable for use
    as ExclusiveStartKey in a DynamoDB Query call.
    """
    padded = cursor + "=" * (4 - len(cursor) % 4) if len(cursor) % 4 else cursor
    decoded = base64.urlsafe_b64decode(padded)
    return json.loads(decoded.decode("utf-8"))


# ---------------------------------------------------------------------------
# Public query functions
# ---------------------------------------------------------------------------

def query_inverter_telemetry(
    asset_id: str,
    site_id: str,
    start: str,
    end: str,
    resolution: str,
    limit: int,
    cursor: Optional[str] = None,
) -> list:
    """
    Query telemetry records for a single inverter.

    For resolution "5min": queries the AssetTimeIndex GSI on
    ona-platform-telemetry-5min using asset_id + timestamp range.

    For resolution "daily": queries the AssetDateIndex GSI on
    ona-platform-telemetry-daily using asset_id + date range.

    Returns records sorted by timestamp ascending with internal fields stripped
    and Decimal values converted to float.
    """
    if resolution == "5min":
        table = _get_table(_TABLE_5MIN)
        key_condition = (
            Key("asset_id").eq(asset_id)
            & Key("timestamp").between(start, end)
        )
        index_name = "AssetTimeIndex"
    else:  # "daily"
        table = _get_table(_TABLE_DAILY)
        key_condition = (
            Key("asset_id").eq(asset_id)
            & Key("date").between(start, end)
        )
        index_name = "AssetDateIndex"

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
        logger.error("DynamoDB query failed for asset_id=%s: %s", asset_id, exc)
        raise

    items = response.get("Items", [])
    cleaned = [_strip_internal_fields(item) for item in items]
    return _convert_decimals(cleaned)


def query_site_telemetry(
    site_id: str,
    start: str,
    end: str,
    resolution: str,
    limit: int,
) -> dict:
    """
    Query telemetry records for all inverters at a site.

    For resolution "5min": queries the primary key on ona-platform-telemetry-5min
    using site_id + asset_ts BETWEEN "{site_id}#{start}" AND "{site_id}#{end}".

    For resolution "daily": queries the primary key on ona-platform-telemetry-daily
    using site_id + asset_date BETWEEN "{site_id}#{start}" AND "{site_id}#{end}".

    Returns a dict mapping asset_id -> list of records sorted by timestamp ascending.
    Internal fields (expires_at) are stripped; Decimal values are converted to float.
    """
    if resolution == "5min":
        table = _get_table(_TABLE_5MIN)
        # Query by site_id (PK) with timestamp filter — asset_ts is asset_id#timestamp
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
            & Key("asset_date").between(sk_start, sk_end)
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

    # Group by asset_id
    result: dict = {}
    for item in items:
        asset_id = item.get("asset_id", "")
        cleaned = _strip_internal_fields(item)
        converted = _convert_decimals(cleaned)
        result.setdefault(asset_id, []).append(converted)

    # Each group is already in ascending order (ScanIndexForward=True)
    return result


def get_data_period(site_id: str, asset_id: str = None) -> dict:
    """
    Return the earliest and latest timestamp for a site or specific inverter.
    Queries ona-platform-telemetry-5min using the appropriate index.
    """
    if asset_id:
        # Query AssetTimeIndex GSI — get first and last record for this asset
        table = _get_table(_TABLE_5MIN)

        # Get earliest
        first_resp = table.query(
            IndexName="AssetTimeIndex",
            KeyConditionExpression=Key("asset_id").eq(asset_id),
            ScanIndexForward=True,
            Limit=1,
        )
        # Get latest
        last_resp = table.query(
            IndexName="AssetTimeIndex",
            KeyConditionExpression=Key("asset_id").eq(asset_id),
            ScanIndexForward=False,
            Limit=1,
        )
        first_items = first_resp.get("Items", [])
        last_items = last_resp.get("Items", [])
        return {
            "site_id": site_id,
            "asset_id": asset_id,
            "first_record": first_items[0]["timestamp"] if first_items else None,
            "last_record": last_items[0]["timestamp"] if last_items else None,
        }
    else:
        # Query by site_id primary key — get first and last record for the site
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
