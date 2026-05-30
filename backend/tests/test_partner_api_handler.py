import json
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from partner_api.lambda_handler import lambda_handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_s3_mock(payload: dict = None, etag: str = '"abc123"'):
    """Return a configured mock_s3 whose get_object returns a body."""
    payload = payload or {"status": "ok"}
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps(payload).encode()
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": etag}
    return mock_s3


def _s3_client_error(code: str):
    return ClientError({"Error": {"Code": code, "Message": code}}, "GetObject")


# ---------------------------------------------------------------------------
# Existing tests (must keep passing)
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_lambda_handler_success(mock_rate_limit, mock_auth, mock_s3):
    # Setup mock S3
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"status": "ok"}'
    mock_s3.get_object.return_value = {
        "Body": mock_body,
        "ETag": '"hash123"'
    }

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "site1"},
        "headers": {"x-api-key": "key123"}
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert response["headers"]["ETag"] == '"hash123"'
    assert json.loads(response["body"]) == {"status": "ok"}
    mock_auth.assert_called_once_with("key123", "site1")

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_lambda_handler_304(mock_rate_limit, mock_auth, mock_s3):
    mock_s3.get_object.side_effect = _s3_client_error("304")

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "site1"},
        "headers": {
            "x-api-key": "key123",
            "if-none-match": '"hash123"'
        }
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 304

@patch("partner_api.lambda_handler.authenticate")
def test_lambda_handler_unauthorized(mock_auth):
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "site1"},
        "headers": {} # Missing x-api-key
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 401


# ---------------------------------------------------------------------------
# HP-1 — /kpi-rollup uses key "{site_id}/kpi-rollup.json" (site_id FIRST)
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp1_kpi_rollup_s3_key_is_site_id_first(mock_rate_limit, mock_auth, mock_s3):
    """GET /kpi-rollup with site_id=Sibaya must call s3.get_object with Key='Sibaya/kpi-rollup.json'."""
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b'{"kpi": 42}'),
        "ETag": '"etag1"',
    }

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "Sibaya"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200, got {response['statusCode']}: {response['body']}"
    )
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key") or call_kwargs[0][1]
    assert actual_key == "Sibaya/kpi-rollup.json", (
        f"Expected Key='Sibaya/kpi-rollup.json', got Key='{actual_key}'. "
        "The handler must use {{site_id}}/{{kind}}.json, not {{kind}}/{{site_id}}.json."
    )


@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp1_kpi_rollup_returns_etag_header(mock_rate_limit, mock_auth, mock_s3):
    """GET /kpi-rollup returns the ETag header from S3 in the response."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"kpi": 1}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-kpi"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "Sibaya"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert response["headers"].get("ETag") == '"etag-kpi"', (
        f"Expected ETag='\"etag-kpi\"' in response headers, got: {response['headers']}"
    )
    assert json.loads(response["body"]) == {"kpi": 1}


# ---------------------------------------------------------------------------
# HP-2 — /maintenance-schedule route exists and uses correct key
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp2_maintenance_schedule_returns_200(mock_rate_limit, mock_auth, mock_s3):
    """GET /maintenance-schedule with valid api_key and site_id returns HTTP 200."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"schedule": []}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-ms"'}

    event = {
        "path": "/maintenance-schedule",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteA"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200, got {response['statusCode']}. "
        "The /maintenance-schedule route must be implemented."
    )


@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp2_maintenance_schedule_s3_key(mock_rate_limit, mock_auth, mock_s3):
    """GET /maintenance-schedule calls s3.get_object with Key='{site_id}/maintenance-schedule.json'."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"schedule": []}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-ms"'}

    site_id = "PlantBeta"
    event = {
        "path": "/maintenance-schedule",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": site_id},
        "headers": {"x-api-key": "validkey"},
    }

    lambda_handler(event, None)

    assert mock_s3.get_object.called, "s3.get_object was never called"
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key")
    assert actual_key == f"{site_id}/maintenance-schedule.json", (
        f"Expected Key='{site_id}/maintenance-schedule.json', got Key='{actual_key}'."
    )


# ---------------------------------------------------------------------------
# HP-3 — /forecast-snapshot uses kind="forecast" (not "forecast-snapshot")
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp3_forecast_snapshot_uses_forecast_kind(mock_rate_limit, mock_auth, mock_s3):
    """GET /forecast-snapshot must call s3.get_object with Key='{site_id}/forecast.json'."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"forecast": []}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-fc"'}

    site_id = "SiteGamma"
    event = {
        "path": "/forecast-snapshot",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": site_id},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200, got {response['statusCode']}: {response['body']}"
    )
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key")
    assert actual_key == f"{site_id}/forecast.json", (
        f"Expected Key='{site_id}/forecast.json' (kind='forecast'), "
        f"got Key='{actual_key}'. The route /forecast-snapshot maps to kind 'forecast', not 'forecast-snapshot'."
    )


# ---------------------------------------------------------------------------
# HP-4 — /maintenance-signals uses correct key layout
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp4_maintenance_signals_s3_key(mock_rate_limit, mock_auth, mock_s3):
    """GET /maintenance-signals calls s3.get_object with Key='{site_id}/maintenance-signals.json'."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"signals": []}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-msi"'}

    site_id = "SiteDelta"
    event = {
        "path": "/maintenance-signals",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": site_id},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200, got {response['statusCode']}: {response['body']}"
    )
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key")
    assert actual_key == f"{site_id}/maintenance-signals.json", (
        f"Expected Key='{site_id}/maintenance-signals.json', got Key='{actual_key}'. "
        "Key must be {{site_id}}/{{kind}}.json, not {{kind}}/{{site_id}}.json."
    )


# ---------------------------------------------------------------------------
# HP-5 — /snapshot with arbitrary kind uses "{site_id}/{kind}.json"
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_hp5_snapshot_generic_key_layout(mock_rate_limit, mock_auth, mock_s3):
    """GET /snapshot?site_id=X&kind=Y calls s3.get_object with Key='X/Y.json'."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"data": "value"}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"etag-snap"'}

    site_id = "SiteEpsilon"
    kind = "custom-report"
    event = {
        "path": "/snapshot",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": site_id, "kind": kind},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200, got {response['statusCode']}: {response['body']}"
    )
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key")
    assert actual_key == f"{site_id}/{kind}.json", (
        f"Expected Key='{site_id}/{kind}.json', got Key='{actual_key}'."
    )


# ---------------------------------------------------------------------------
# EC-1 — NoSuchKey from S3 → HTTP 404
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_ec1_no_such_key_returns_404(mock_rate_limit, mock_auth, mock_s3):
    """When S3 raises ClientError NoSuchKey the handler returns HTTP 404."""
    mock_s3.get_object.side_effect = _s3_client_error("NoSuchKey")

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "MissingSite"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 404, (
        f"Expected 404 for NoSuchKey, got {response['statusCode']}"
    )


# ---------------------------------------------------------------------------
# EC-2 — NotModified (code "304") from S3 → HTTP 304
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_ec2_not_modified_code_304_returns_304(mock_rate_limit, mock_auth, mock_s3):
    """ClientError with code '304' returns HTTP 304 (string code variant)."""
    mock_s3.get_object.side_effect = _s3_client_error("304")

    event = {
        "path": "/maintenance-signals",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteA"},
        "headers": {"x-api-key": "validkey", "if-none-match": '"old-etag"'},
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 304, (
        f"Expected 304 for code='304' ClientError, got {response['statusCode']}"
    )


@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_ec2_not_modified_code_notmodified_returns_304(mock_rate_limit, mock_auth, mock_s3):
    """ClientError with code 'NotModified' returns HTTP 304 (string code variant)."""
    mock_s3.get_object.side_effect = _s3_client_error("NotModified")

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteB"},
        "headers": {"x-api-key": "validkey", "if-none-match": '"stale-etag"'},
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 304, (
        f"Expected 304 for code='NotModified' ClientError, got {response['statusCode']}"
    )


# ---------------------------------------------------------------------------
# EH-1 — Missing x-api-key header → HTTP 401
# ---------------------------------------------------------------------------

def test_eh1_missing_api_key_returns_401():
    """A request with no x-api-key header returns HTTP 401 without touching S3."""
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "AnySite"},
        "headers": {},
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 401, (
        f"Expected 401 for missing api key, got {response['statusCode']}"
    )


def test_eh1_empty_api_key_returns_401():
    """A request with an empty x-api-key value returns HTTP 401."""
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "AnySite"},
        "headers": {"x-api-key": ""},
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 401, (
        f"Expected 401 for empty api key, got {response['statusCode']}"
    )


# ---------------------------------------------------------------------------
# INV-1 — Bucket name is always passed to s3.get_object
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_inv1_bucket_passed_to_get_object(mock_rate_limit, mock_auth, mock_s3):
    """s3.get_object is always called with a Bucket keyword argument."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"ok": true}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"e"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteX"},
        "headers": {"x-api-key": "validkey"},
    }
    lambda_handler(event, None)

    call_kwargs = mock_s3.get_object.call_args
    bucket = call_kwargs.kwargs.get("Bucket") or call_kwargs[1].get("Bucket")
    assert bucket is not None and bucket != "", (
        "s3.get_object must be called with a non-empty Bucket argument."
    )


# ---------------------------------------------------------------------------
# INV-2 — IfNoneMatch is forwarded when If-None-Match request header is present
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_inv2_if_none_match_forwarded_to_s3(mock_rate_limit, mock_auth, mock_s3):
    """When If-None-Match header is present, IfNoneMatch is forwarded to s3.get_object."""
    mock_s3.get_object.side_effect = _s3_client_error("304")

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteY"},
        "headers": {"x-api-key": "validkey", "if-none-match": '"my-etag"'},
    }
    lambda_handler(event, None)

    call_kwargs = mock_s3.get_object.call_args
    if_none_match = call_kwargs.kwargs.get("IfNoneMatch") or call_kwargs[1].get("IfNoneMatch")
    assert if_none_match == '"my-etag"', (
        f"Expected IfNoneMatch='\"my-etag\"' forwarded to s3.get_object, got: {if_none_match}"
    )


# ===========================================================================
# NEW TESTS — CORS, multi-word site_id, traversal rejection
# ===========================================================================

# ---------------------------------------------------------------------------
# CORS-1 — Access-Control-Allow-Origin: * on a 200 /kpi-rollup response
#           Also verifies CORS is additive (ETag and Content-Type still present)
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_cors1_200_response_has_cors_header(mock_rate_limit, mock_auth, mock_s3):
    """A 200 response from /kpi-rollup must include Access-Control-Allow-Origin: *."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"kpi": 1}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"cors-etag"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteCorA"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert response["headers"].get("Access-Control-Allow-Origin") == "*", (
        f"Expected Access-Control-Allow-Origin: * on 200 response, "
        f"got headers: {response['headers']}"
    )


@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_cors1_200_response_cors_is_additive_etag_and_content_type_still_present(
    mock_rate_limit, mock_auth, mock_s3
):
    """CORS header is additive: ETag and Content-Type must still be present on the 200 response."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"kpi": 2}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"additive-etag"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "SiteCorB"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    headers = response["headers"]
    assert headers.get("Access-Control-Allow-Origin") == "*", (
        f"Missing CORS header; headers: {headers}"
    )
    assert headers.get("ETag") == '"additive-etag"', (
        f"ETag disappeared after CORS was added; headers: {headers}"
    )
    assert headers.get("Content-Type") == "application/json", (
        f"Content-Type disappeared after CORS was added; headers: {headers}"
    )


# ---------------------------------------------------------------------------
# CORS-2 — Access-Control-Allow-Origin: * on a 401 (missing x-api-key)
# ---------------------------------------------------------------------------

def test_cors2_401_missing_api_key_has_cors_header():
    """A 401 response (missing x-api-key) must include Access-Control-Allow-Origin: *."""
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "AnySite"},
        "headers": {},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 401
    assert response["headers"].get("Access-Control-Allow-Origin") == "*", (
        f"Expected Access-Control-Allow-Origin: * on 401 response, "
        f"got headers: {response['headers']}"
    )


# ---------------------------------------------------------------------------
# CORS-3 — Access-Control-Allow-Origin: * on a 404 (NoSuchKey from S3)
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_cors3_404_no_such_key_has_cors_header(mock_rate_limit, mock_auth, mock_s3):
    """A 404 response (S3 NoSuchKey) must include Access-Control-Allow-Origin: *."""
    mock_s3.get_object.side_effect = _s3_client_error("NoSuchKey")

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "GhostSite"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 404
    assert response["headers"].get("Access-Control-Allow-Origin") == "*", (
        f"Expected Access-Control-Allow-Origin: * on 404 response, "
        f"got headers: {response['headers']}"
    )


# ---------------------------------------------------------------------------
# SPACE-1 — Multi-word site_id with spaces is accepted → HTTP 200
#            S3 key must use the literal site_id including spaces
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_space1_site_id_with_spaces_returns_200(mock_rate_limit, mock_auth, mock_s3):
    """GET /kpi-rollup with site_id='Sibaya Main Campus' must return HTTP 200."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"kpi": 99}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"space-etag"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "Sibaya Main Campus"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 200, (
        f"Expected 200 for site_id with spaces, got {response['statusCode']}: {response['body']}. "
        "The validator must allow spaces in site_id."
    )


@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_space1_site_id_with_spaces_uses_correct_s3_key(mock_rate_limit, mock_auth, mock_s3):
    """GET /kpi-rollup with site_id='Sibaya Main Campus' must call s3.get_object with Key='Sibaya Main Campus/kpi-rollup.json'."""
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"kpi": 99}'
    mock_s3.get_object.return_value = {"Body": mock_body, "ETag": '"space-etag"'}

    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "Sibaya Main Campus"},
        "headers": {"x-api-key": "validkey"},
    }

    lambda_handler(event, None)

    assert mock_s3.get_object.called, "s3.get_object was not called at all"
    call_kwargs = mock_s3.get_object.call_args
    actual_key = call_kwargs.kwargs.get("Key") or call_kwargs[1].get("Key")
    assert actual_key == "Sibaya Main Campus/kpi-rollup.json", (
        f"Expected Key='Sibaya Main Campus/kpi-rollup.json', got Key='{actual_key}'. "
        "The site_id with spaces must pass through to S3 unchanged."
    )


# ---------------------------------------------------------------------------
# TRAVERSAL-1 — site_id containing "/" is rejected with HTTP 400, S3 not called
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_traversal1_forward_slash_in_site_id_returns_400(mock_rate_limit, mock_auth, mock_s3):
    """site_id='a/b' must return HTTP 400 and must NOT call s3.get_object."""
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "a/b"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400, (
        f"Expected 400 for site_id='a/b', got {response['statusCode']}"
    )
    mock_s3.get_object.assert_not_called()


# ---------------------------------------------------------------------------
# TRAVERSAL-2 — site_id containing ".." is rejected with HTTP 400, S3 not called
# ---------------------------------------------------------------------------

@patch("partner_api.lambda_handler.s3")
@patch("partner_api.lambda_handler.authenticate")
@patch("partner_api.lambda_handler.check_rate_limit")
def test_traversal2_dotdot_in_site_id_returns_400(mock_rate_limit, mock_auth, mock_s3):
    """site_id='../secret' must return HTTP 400 and must NOT call s3.get_object."""
    event = {
        "path": "/kpi-rollup",
        "httpMethod": "GET",
        "queryStringParameters": {"site_id": "../secret"},
        "headers": {"x-api-key": "validkey"},
    }

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400, (
        f"Expected 400 for site_id='../secret', got {response['statusCode']}"
    )
    mock_s3.get_object.assert_not_called()
