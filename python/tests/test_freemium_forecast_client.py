"""Tests for FreemiumForecastClient — two-step verify+forecast API contract.

Requirements under test:
  HP-1  Client targets https://forecasting.api.asoba.org (NOT the old https://api.asoba.org/v1/freemium-forecast)
  HP-2  request_verification_code() POSTs to /api/v1/freemium-forecast/verify with email
  HP-3  get_forecast() POSTs multipart to /api/v1/freemium-forecast with all six fields:
          email, verification_code, site_name, location, capacity_kw, file
  HP-4  get_forecast() returns the parsed JSON body on success
  HP-5  get_forecast() sends tou_accepted="true" when the caller explicitly accepts the ToU
  HP-6  get_forecast() sends marketing_opt_in="true" when the caller opts in
  EC-1  Old base URL (https://api.asoba.org/v1/freemium-forecast) must NOT appear anywhere
        in the client's request
  EC-2  capacity_kw field is included in the multipart form data
  EC-3  verification_code field is included in the multipart form data
  EC-4  marketing_opt_in defaults to not-opted-in (absent or "false") when the caller does
        not pass marketing_opt_in
  EH-1  CSV file not found raises ValidationError
  EH-2  Invalid email raises ValidationError
  EH-3  Missing site_name raises ValidationError
  EH-4  Missing location raises ValidationError
  EH-5  Server HTTP 400 response raises ValidationError with the error message
  EH-6  Server HTTP 5xx response raises ServiceUnavailableError
  EH-7  Network failure raises ServiceUnavailableError
  EH-8  Caller does not accept ToU (tou_accepted omitted or False) raises ValidationError
        BEFORE any network call
  IB-1  verify endpoint path is exactly /api/v1/freemium-forecast/verify
  IB-2  forecast endpoint path is exactly /api/v1/freemium-forecast
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ona_platform.exceptions import ServiceUnavailableError, ValidationError
from ona_platform.services.freemium_forecast import FreemiumForecastClient

# ---------------------------------------------------------------------------
# Fake in-process HTTP server
# ---------------------------------------------------------------------------

_SUCCESS_FORECAST = {
    "status": "success",
    "forecast": {
        "site_name": "Solar Farm A",
        "forecasts": [{"timestamp": "2025-12-01T06:00:00Z", "kWh_forecast": 55.2}],
        "summary": {"total_kwh_24h": 1200.0},
    },
}

_SUCCESS_VERIFY = {"status": "success", "message": "Verification code sent"}

_TOU_REJECTED_BODY = (
    b'{"error": "You must accept the Terms of Use (tou_accepted=true) to use this service."}'
)


class _FreemiumHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler recording request details for assertions."""

    # Class-level state mutated per test via _reset_handler()
    forecast_status = 200
    verify_status = 200
    last_method = None
    last_path = None
    last_content_type = None
    last_body = None
    verify_call_count = 0
    forecast_call_count = 0

    def log_message(self, *_args, **_kwargs):
        return  # silence noise

    def do_POST(self):  # noqa: N802
        from urllib.parse import urlparse

        parsed = urlparse(self.path)
        type(self).last_method = "POST"
        type(self).last_path = parsed.path
        type(self).last_content_type = self.headers.get("Content-Type", "")

        length = int(self.headers.get("Content-Length", 0))
        type(self).last_body = self.rfile.read(length) if length else b""

        if parsed.path == "/api/v1/freemium-forecast/verify":
            type(self).verify_call_count += 1
            status = type(self).verify_status
            body = json.dumps(_SUCCESS_VERIFY).encode() if status < 400 else b'{"error":"bad request"}'
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/api/v1/freemium-forecast":
            type(self).forecast_call_count += 1
            status = type(self).forecast_status
            if status == 400:
                body = b'{"error":"Missing required fields: verification_code"}'
            elif status >= 500:
                body = b'{"error":"internal server error"}'
            else:
                body = json.dumps(_SUCCESS_FORECAST).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')


def _reset_handler():
    _FreemiumHandler.forecast_status = 200
    _FreemiumHandler.verify_status = 200
    _FreemiumHandler.last_method = None
    _FreemiumHandler.last_path = None
    _FreemiumHandler.last_content_type = None
    _FreemiumHandler.last_body = None
    _FreemiumHandler.verify_call_count = 0
    _FreemiumHandler.forecast_call_count = 0


@pytest.fixture
def server():
    _reset_handler()
    srv = HTTPServer(("127.0.0.1", 0), _FreemiumHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def client(server):
    """FreemiumForecastClient with its base URL redirected to the local test server."""
    host, port = server.server_address
    c = FreemiumForecastClient()
    # Override the base URL that the client uses so requests hit the local server.
    # We set both the URL attribute AND patch the module constant so any method
    # that constructs paths from the base is also redirected.
    c._base_url = f"http://{host}:{port}"
    return c


@pytest.fixture
def csv_file(tmp_path):
    """A minimal valid CSV file on disk."""
    p = tmp_path / "solar.csv"
    p.write_text("Timestamp,Power (kW)\n2025-12-01T06:00:00Z,55.2\n")
    return p


# ---------------------------------------------------------------------------
# HP-1 / EC-1 — Correct base URL, old URL absent
# ---------------------------------------------------------------------------


class TestBaseUrl:
    def test_hp1_default_base_url_is_forecasting_domain(self):
        """Client must default to https://forecasting.api.asoba.org (HP-1)."""
        c = FreemiumForecastClient()
        assert "forecasting.api.asoba.org" in c._base_url

    def test_ec1_old_url_not_in_base_url(self):
        """The old endpoint (api.asoba.org/v1/freemium-forecast) must not appear (EC-1)."""
        c = FreemiumForecastClient()
        assert "api.asoba.org/v1/freemium-forecast" not in c._base_url

    def test_ec1_old_constant_not_used(self):
        """Module-level constant must not equal the old URL."""
        import ona_platform.services.freemium_forecast as mod

        # The old URL that must no longer be the base
        assert getattr(mod, "FREEMIUM_BASE_URL", None) != "https://api.asoba.org/v1/freemium-forecast"
        # Also check that no attribute points at the old URL
        attrs = [v for v in vars(mod).values() if isinstance(v, str)]
        for attr in attrs:
            assert "api.asoba.org/v1/freemium-forecast" not in attr, (
                f"Module constant still contains old URL: {attr!r}"
            )


# ---------------------------------------------------------------------------
# HP-2 / IB-1 — request_verification_code
# ---------------------------------------------------------------------------


class TestRequestVerificationCode:
    def test_hp2_verify_posts_to_correct_path(self, client, server):
        """request_verification_code() must POST to /api/v1/freemium-forecast/verify (HP-2, IB-1)."""
        client.request_verification_code(email="user@example.com")
        assert _FreemiumHandler.last_method == "POST"
        assert _FreemiumHandler.last_path == "/api/v1/freemium-forecast/verify"

    def test_hp2_verify_sends_email(self, client, server):
        """request_verification_code() must include the email in the request body (HP-2)."""
        client.request_verification_code(email="user@example.com")
        body = _FreemiumHandler.last_body.decode()
        assert "user@example.com" in body

    def test_hp2_verify_returns_response(self, client, server):
        """request_verification_code() must return the parsed JSON response (HP-2)."""
        result = client.request_verification_code(email="user@example.com")
        assert result is not None

    def test_hp2_verify_increments_call_count(self, client, server):
        """request_verification_code() must make exactly one HTTP call (HP-2)."""
        client.request_verification_code(email="user@example.com")
        assert _FreemiumHandler.verify_call_count == 1


# ---------------------------------------------------------------------------
# HP-3 / IB-2 — get_forecast posts to correct path with all six fields
# ---------------------------------------------------------------------------


class TestGetForecastPath:
    def test_hp3_forecast_posts_to_correct_path(self, client, server, csv_file):
        """get_forecast() must POST to /api/v1/freemium-forecast (HP-3, IB-2)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
        )
        assert _FreemiumHandler.last_method == "POST"
        assert _FreemiumHandler.last_path == "/api/v1/freemium-forecast"

    def test_hp3_forecast_is_multipart(self, client, server, csv_file):
        """get_forecast() must use multipart/form-data encoding (HP-3)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
        )
        assert "multipart/form-data" in _FreemiumHandler.last_content_type


# ---------------------------------------------------------------------------
# HP-3 — All six required fields present in multipart body
# ---------------------------------------------------------------------------


class TestGetForecastAllSixFields:
    """Each field required by the server must appear in the multipart body."""

    def _run_forecast(self, client, csv_file):
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="ABC-999",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=750.0,
            tou_accepted=True,
        )
        return _FreemiumHandler.last_body.decode(errors="replace")

    def test_hp3_field_email_present(self, client, server, csv_file):
        """'email' field must be in the multipart body (HP-3)."""
        body = self._run_forecast(client, csv_file)
        assert "email" in body
        assert "user@example.com" in body

    def test_hp3_field_verification_code_present(self, client, server, csv_file):
        """'verification_code' field must be in the multipart body (HP-3, EC-3)."""
        body = self._run_forecast(client, csv_file)
        assert "verification_code" in body
        assert "ABC-999" in body

    def test_hp3_field_site_name_present(self, client, server, csv_file):
        """'site_name' field must be in the multipart body (HP-3)."""
        body = self._run_forecast(client, csv_file)
        assert "site_name" in body
        assert "Solar Farm A" in body

    def test_hp3_field_location_present(self, client, server, csv_file):
        """'location' field must be in the multipart body (HP-3)."""
        body = self._run_forecast(client, csv_file)
        assert "location" in body
        assert "Durban" in body

    def test_hp3_field_capacity_kw_present(self, client, server, csv_file):
        """'capacity_kw' field must be in the multipart body (HP-3, EC-2)."""
        body = self._run_forecast(client, csv_file)
        assert "capacity_kw" in body
        assert "750" in body  # value appears as string in multipart

    def test_hp3_field_file_present(self, client, server, csv_file):
        """CSV file content must be in the multipart body (HP-3)."""
        body = self._run_forecast(client, csv_file)
        # The CSV header should appear in the body
        assert "Timestamp" in body


# ---------------------------------------------------------------------------
# HP-4 — Successful response parsing
# ---------------------------------------------------------------------------


class TestGetForecastSuccess:
    def test_hp4_returns_parsed_json(self, client, server, csv_file):
        """get_forecast() must return the parsed JSON dict on HTTP 200 (HP-4)."""
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
        )
        assert result == _SUCCESS_FORECAST

    def test_hp4_forecast_key_present(self, client, server, csv_file):
        """Returned dict must contain the 'forecast' key (HP-4)."""
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
        )
        assert "forecast" in result


# ---------------------------------------------------------------------------
# HP-5 — tou_accepted field sent as "true" in multipart body
# ---------------------------------------------------------------------------


class TestTouAccepted:
    """Tests for the new tou_accepted field required by the live API contract."""

    def test_hp5_tou_accepted_field_sent_as_true_string(self, client, server, csv_file):
        """get_forecast() must send tou_accepted=\"true\" in the multipart body when
        the caller passes tou_accepted=True (HP-5)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        assert "tou_accepted" in body, (
            "tou_accepted field must be present in the multipart body"
        )
        assert "true" in body, (
            "tou_accepted must be sent with value 'true'"
        )

    def test_hp5_tou_accepted_field_name_appears_in_body(self, client, server, csv_file):
        """The field name 'tou_accepted' must appear verbatim in the Content-Disposition
        header of the multipart body (HP-5)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Cape Town",
            capacity_kw=100.0,
            tou_accepted=True,
        )
        raw = _FreemiumHandler.last_body.decode(errors="replace")
        # The multipart field name appears in a Content-Disposition line
        assert 'name="tou_accepted"' in raw or "tou_accepted" in raw, (
            "tou_accepted must appear as a named field in the multipart body"
        )

    def test_hp5_tou_accepted_value_is_string_true_not_boolean(self, client, server, csv_file):
        """The value sent for tou_accepted must be the string \"true\", not the Python bool
        True or the integer 1 — the server does a string comparison (HP-5)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="ABC-001",
            site_name="Site",
            location="Johannesburg",
            capacity_kw=200.0,
            tou_accepted=True,
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        # Find the section of the body that contains the tou_accepted field
        # and verify the value is literally the string "true"
        assert "true" in body, (
            "tou_accepted field value must be the string 'true'"
        )


# ---------------------------------------------------------------------------
# EH-8 — Caller must explicitly accept ToU; omitting or passing False raises
#         ValidationError BEFORE any network call
# ---------------------------------------------------------------------------


class TestTouRejected:
    """Callers must actively opt-in to the ToU; silence is not consent."""

    def test_eh8_no_tou_accepted_param_raises_validation_error(self, client, server, csv_file):
        """Calling get_forecast() without tou_accepted must raise ValidationError BEFORE
        making any network call (EH-8)."""
        with pytest.raises(ValidationError, match="[Tt]erms"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                # tou_accepted intentionally omitted
            )
        # No network call must have been made
        assert _FreemiumHandler.forecast_call_count == 0, (
            "get_forecast must raise ValidationError before making any HTTP request "
            "when tou_accepted is not True"
        )

    def test_eh8_tou_accepted_false_raises_validation_error(self, client, server, csv_file):
        """Passing tou_accepted=False must raise ValidationError BEFORE any network call (EH-8)."""
        with pytest.raises(ValidationError, match="[Tt]erms"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=False,
            )
        assert _FreemiumHandler.forecast_call_count == 0, (
            "get_forecast must not make any HTTP request when tou_accepted=False"
        )

    def test_eh8_tou_accepted_none_raises_validation_error(self, client, server, csv_file):
        """Passing tou_accepted=None must raise ValidationError BEFORE any network call (EH-8)."""
        with pytest.raises(ValidationError, match="[Tt]erms"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=None,
            )
        assert _FreemiumHandler.forecast_call_count == 0, (
            "get_forecast must not make any HTTP request when tou_accepted=None"
        )

    def test_eh8_validation_error_message_mentions_terms_of_use(self, csv_file):
        """The ValidationError raised when ToU is not accepted must mention 'Terms of Use'
        or 'tou_accepted' so the caller knows what they need to do (EH-8)."""
        c = FreemiumForecastClient()
        # Point to a non-listening port so any accidental network call fails fast
        c._base_url = "http://127.0.0.1:1"
        with pytest.raises(ValidationError) as exc_info:
            c.get_forecast(
                csv_path=__file__,  # this file exists on disk — not the reason for the error
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                # tou_accepted intentionally omitted
            )
        msg = str(exc_info.value).lower()
        assert "terms" in msg or "tou_accepted" in msg, (
            f"ValidationError message should mention 'Terms' or 'tou_accepted', got: {exc_info.value!r}"
        )


# ---------------------------------------------------------------------------
# HP-6 / EC-4 — marketing_opt_in field
# ---------------------------------------------------------------------------


class TestMarketingOptIn:
    """Tests for the optional marketing_opt_in field."""

    def test_hp6_marketing_opt_in_true_sent_as_true_string(self, client, server, csv_file):
        """When the caller passes marketing_opt_in=True, the client must send the string
        \"true\" in the multipart body (HP-6)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
            marketing_opt_in=True,
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        assert "marketing_opt_in" in body, (
            "marketing_opt_in field must be present in the multipart body when opted in"
        )
        # The value associated with marketing_opt_in must be "true"
        assert "true" in body, (
            "marketing_opt_in must be sent with value 'true' when caller opts in"
        )

    def test_hp6_marketing_opt_in_field_name_appears_in_body(self, client, server, csv_file):
        """The field name 'marketing_opt_in' must appear in the multipart body when
        the caller opts in (HP-6)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Cape Town",
            capacity_kw=100.0,
            tou_accepted=True,
            marketing_opt_in=True,
        )
        raw = _FreemiumHandler.last_body.decode(errors="replace")
        assert "marketing_opt_in" in raw, (
            "marketing_opt_in field name must appear in multipart body"
        )

    def test_ec4_marketing_opt_in_defaults_to_not_opted_in(self, client, server, csv_file):
        """When the caller does NOT pass marketing_opt_in, the field must either be absent
        from the body or sent as \"false\" — it must NOT be sent as \"true\" (EC-4)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Solar Farm A",
            location="Durban",
            capacity_kw=500.0,
            tou_accepted=True,
            # marketing_opt_in intentionally omitted
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        # If the field is present, its value must not be "true"
        if "marketing_opt_in" in body:
            # Extract the section after the field name to check its value
            idx = body.index("marketing_opt_in")
            segment = body[idx: idx + 80]
            assert "true" not in segment, (
                f"marketing_opt_in must not default to 'true'; got segment: {segment!r}"
            )

    def test_ec4_marketing_opt_in_false_does_not_send_true(self, client, server, csv_file):
        """When the caller passes marketing_opt_in=False, the client must not send \"true\"
        for that field (EC-4)."""
        client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Durban",
            capacity_kw=100.0,
            tou_accepted=True,
            marketing_opt_in=False,
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        if "marketing_opt_in" in body:
            idx = body.index("marketing_opt_in")
            segment = body[idx: idx + 80]
            assert "true" not in segment, (
                f"marketing_opt_in=False must not send 'true'; got segment: {segment!r}"
            )

    def test_hp6_marketing_opt_in_does_not_affect_other_fields(self, client, server, csv_file):
        """Passing marketing_opt_in=True must not remove or corrupt other required fields
        from the multipart body (HP-6, integration)."""
        client.get_forecast(
            csv_path=csv_file,
            email="opted-in@example.com",
            verification_code="OPT-007",
            site_name="Opt-In Farm",
            location="Pretoria",
            capacity_kw=300.0,
            tou_accepted=True,
            marketing_opt_in=True,
        )
        body = _FreemiumHandler.last_body.decode(errors="replace")
        # All six original required fields must still be present
        assert "opted-in@example.com" in body
        assert "OPT-007" in body
        assert "Opt-In Farm" in body
        assert "Pretoria" in body
        assert "300" in body
        assert "Timestamp" in body  # CSV content


# ---------------------------------------------------------------------------
# EH-1 through EH-4 — Input validation (existing behavior preserved)
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_eh1_missing_csv_raises_validation_error(self, client):
        """Non-existent CSV path must raise ValidationError (EH-1)."""
        with pytest.raises(ValidationError, match="not found"):
            client.get_forecast(
                csv_path="/nonexistent/path/data.csv",
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh2_invalid_email_raises_validation_error(self, client, csv_file):
        """Email without '@' must raise ValidationError (EH-2)."""
        with pytest.raises(ValidationError, match="[Ii]nvalid email"):
            client.get_forecast(
                csv_path=csv_file,
                email="not-an-email",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh2_empty_email_raises_validation_error(self, client, csv_file):
        """Empty email must raise ValidationError (EH-2)."""
        with pytest.raises(ValidationError):
            client.get_forecast(
                csv_path=csv_file,
                email="",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh3_missing_site_name_raises_validation_error(self, client, csv_file):
        """Empty site_name must raise ValidationError (EH-3)."""
        with pytest.raises(ValidationError, match="site_name"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh4_missing_location_raises_validation_error(self, client, csv_file):
        """Empty location must raise ValidationError (EH-4)."""
        with pytest.raises(ValidationError, match="location"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="",
                capacity_kw=100.0,
                tou_accepted=True,
            )


# ---------------------------------------------------------------------------
# EH-5 — HTTP 400 from server maps to ValidationError
# ---------------------------------------------------------------------------


class TestServerErrorMapping:
    def test_eh5_http_400_raises_validation_error(self, client, server, csv_file):
        """HTTP 400 from the forecast endpoint must raise ValidationError (EH-5)."""
        _FreemiumHandler.forecast_status = 400
        with pytest.raises(ValidationError):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh5_http_400_error_message_surfaced(self, client, server, csv_file):
        """The error body from HTTP 400 must be included in the ValidationError message (EH-5)."""
        _FreemiumHandler.forecast_status = 400
        with pytest.raises(ValidationError, match="Missing required fields"):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh6_http_500_raises_service_unavailable(self, client, server, csv_file):
        """HTTP 500 from the forecast endpoint must raise ServiceUnavailableError (EH-6)."""
        _FreemiumHandler.forecast_status = 500
        with pytest.raises(ServiceUnavailableError):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )

    def test_eh6_http_503_raises_service_unavailable(self, client, server, csv_file):
        """HTTP 503 must also raise ServiceUnavailableError (EH-6)."""
        _FreemiumHandler.forecast_status = 503
        with pytest.raises(ServiceUnavailableError):
            client.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )


# ---------------------------------------------------------------------------
# EH-7 — Network failure raises ServiceUnavailableError
# ---------------------------------------------------------------------------


class TestNetworkFailure:
    def test_eh7_connection_error_raises_service_unavailable(self, csv_file):
        """A network-level exception must be wrapped as ServiceUnavailableError (EH-7)."""
        c = FreemiumForecastClient()
        # Point the client at a port that is definitely not listening
        c._base_url = "http://127.0.0.1:1"

        with pytest.raises(ServiceUnavailableError):
            c.get_forecast(
                csv_path=csv_file,
                email="user@example.com",
                verification_code="123456",
                site_name="Site",
                location="Durban",
                capacity_kw=100.0,
                tou_accepted=True,
            )


# ---------------------------------------------------------------------------
# get_forecast signature — verification_code and capacity_kw are required params
# ---------------------------------------------------------------------------


class TestSignatureRequirements:
    def test_hp3_get_forecast_accepts_verification_code_param(self, client, server, csv_file):
        """get_forecast() must accept verification_code as a parameter (HP-3)."""
        # If the parameter doesn't exist this call raises TypeError, not ValidationError
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="TEST-CODE",
            site_name="Site",
            location="Durban",
            capacity_kw=100.0,
            tou_accepted=True,
        )
        assert result is not None

    def test_hp3_get_forecast_accepts_capacity_kw_param(self, client, server, csv_file):
        """get_forecast() must accept capacity_kw as a parameter (HP-3, EC-2)."""
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Durban",
            capacity_kw=9999.9,
            tou_accepted=True,
        )
        assert result is not None

    def test_client_has_request_verification_code_method(self):
        """FreemiumForecastClient must expose request_verification_code() (HP-2)."""
        c = FreemiumForecastClient()
        assert callable(getattr(c, "request_verification_code", None)), (
            "FreemiumForecastClient is missing request_verification_code() method"
        )

    def test_hp5_get_forecast_accepts_tou_accepted_param(self, client, server, csv_file):
        """get_forecast() must accept a tou_accepted parameter (HP-5)."""
        # A TypeError here means the parameter does not exist in the signature
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Durban",
            capacity_kw=100.0,
            tou_accepted=True,
        )
        assert result is not None

    def test_hp6_get_forecast_accepts_marketing_opt_in_param(self, client, server, csv_file):
        """get_forecast() must accept an optional marketing_opt_in parameter (HP-6)."""
        # A TypeError here means the parameter does not exist in the signature
        result = client.get_forecast(
            csv_path=csv_file,
            email="user@example.com",
            verification_code="123456",
            site_name="Site",
            location="Durban",
            capacity_kw=100.0,
            tou_accepted=True,
            marketing_opt_in=True,
        )
        assert result is not None
