# Code Integrity Audit Report

> **Generated**: 2026-08-08 08:13:15  
> **Target**: `/Users/shingi/Workbench/sdk`  
> **Status**: 🟢 **PASS**

---

## 1. Executive Summary

| Metric | Value | Status |
| :--- | :--- | :--- |
| **Audit Status** | `PASS` | 🟢 **PASS** |
| **Critical Failures** | `0` | ✅ Clean |
| **Warnings / Findings** | `718` | Advisory |
| **Report JSON** | `8-8-2026-001-audit-report.json` | Saved to `.review/` |

## 2. TEST SUITE AUTHENTICITY CLASSIFICATION

| Tier | Classification | Count | Percentage | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Live AWS / E2E Integration** | `0` | `0.0%` | Real network/AWS SDK calls (`boto3`, live endpoints, dryRun). **Gold Standard**. |
| **Tier 2** | **Contract-Enforced Behavioral** | `162` | `64.5%` | Calls actual code directly with schema assertions ($k_t$, keys, ranges). |
| **Tier 3** | **Mock Theater / Superficial** | `89` | `35.5%` | Mocks internal code or lacks substantive outcome assertions. |

> [!IMPORTANT]
> **Tier 3 Mock Theater Ratio**: `35.5%` of tests in the repository use internal mocks or lack payload checks.

## 3. Lifecycle Parity & Resource Teardown

✅ *No issues found in this category.*

## 4. Behavioral Test Authenticity (Anti-Mock Theater)

| Severity | File / Line | Rule | Details |
| :--- | :--- | :--- | :--- |
| 🟡 WARN | `backend/tests/test_auth.py`:L55 | `ASSERTION_THEATER` | Test 'test_raises_auth_error_when_key_missing' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_auth.py`:L62 | `ASSERTION_THEATER` | Test 'test_raises_auth_error_when_key_expired' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_auth.py`:L82 | `ASSERTION_THEATER` | Test 'test_invalid_expires_at_format_treated_as_expired' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_auth.py`:L90 | `ASSERTION_THEATER` | Test 'test_raises_forbidden_when_site_not_permitted' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_auth.py`:L102 | `ASSERTION_THEATER` | Test 'test_empty_permitted_site_ids_raises_forbidden' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_auth.py`:L141 | `ASSERTION_THEATER` | Test 'test_dynamodb_error_raises_auth_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L132 | `ASSERTION_THEATER` | Test 'test_invalid_asset_id_special_chars_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L137 | `ASSERTION_THEATER` | Test 'test_invalid_asset_id_slash_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L142 | `ASSERTION_THEATER` | Test 'test_invalid_site_id_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L147 | `ASSERTION_THEATER` | Test 'test_inverted_time_range_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L156 | `ASSERTION_THEATER` | Test 'test_time_range_exceeding_31_days_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L165 | `ASSERTION_THEATER` | Test 'test_limit_exceeding_1000_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L213 | `ASSERTION_THEATER` | Test 'test_missing_site_id_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L218 | `ASSERTION_THEATER` | Test 'test_missing_start_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L223 | `ASSERTION_THEATER` | Test 'test_missing_end_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L244 | `ASSERTION_THEATER` | Test 'test_60_calls_succeed' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L249 | `ASSERTION_THEATER` | Test 'test_61st_call_raises_rate_limit_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L256 | `ASSERTION_THEATER` | Test 'test_counter_resets_after_window_expires' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L272 | `ASSERTION_THEATER` | Test 'test_different_keys_have_independent_counters' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L306 | `ASSERTION_THEATER` | Test 'test_malformed_cursor_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L310 | `ASSERTION_THEATER` | Test 'test_cursor_missing_asset_id_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L316 | `ASSERTION_THEATER` | Test 'test_cursor_missing_timestamp_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `backend/tests/test_handler.py`:L322 | `ASSERTION_THEATER` | Test 'test_cursor_asset_id_mismatch_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L134 | `ASSERTION_THEATER` | Test 'test_login_service_unavailable_raises_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L271 | `ASSERTION_THEATER` | Test 'test_logout_clears_token' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L277 | `ASSERTION_THEATER` | Test 'test_is_authenticated_returns_true_with_token' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L282 | `ASSERTION_THEATER` | Test 'test_is_authenticated_returns_false_without_token' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L308 | `ASSERTION_THEATER` | Test 'test_refresh_token_invalid_token_raises_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L372 | `ASSERTION_THEATER` | Test 'test_auth_client_lazy_loaded' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L401 | `ASSERTION_THEATER` | Test 'test_auth_client_requires_endpoint' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L410 | `ASSERTION_THEATER` | Test 'test_auth_client_accepts_https_endpoint' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L416 | `ASSERTION_THEATER` | Test 'test_auth_client_rejects_http_endpoint' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L432 | `ASSERTION_THEATER` | Test 'test_login_network_error_raises_service_unavailable' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L438 | `ASSERTION_THEATER` | Test 'test_mfa_verification_network_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_auth_client.py`:L538 | `ASSERTION_THEATER` | Test 'test_logout_invalidates_token' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_client.py`:L19 | `ASSERTION_THEATER` | Test 'test_lazy_service_loading' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L207 | `ASSERTION_THEATER` | Test 'test_hp2_verify_returns_response' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L611 | `ASSERTION_THEATER` | Test 'test_eh1_missing_csv_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L624 | `ASSERTION_THEATER` | Test 'test_eh2_invalid_email_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L637 | `ASSERTION_THEATER` | Test 'test_eh2_empty_email_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L650 | `ASSERTION_THEATER` | Test 'test_eh3_missing_site_name_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L663 | `ASSERTION_THEATER` | Test 'test_eh4_missing_location_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L683 | `ASSERTION_THEATER` | Test 'test_eh5_http_400_raises_validation_error' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L697 | `ASSERTION_THEATER` | Test 'test_eh5_http_400_error_message_surfaced' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L711 | `ASSERTION_THEATER` | Test 'test_eh6_http_500_raises_service_unavailable' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L725 | `ASSERTION_THEATER` | Test 'test_eh6_http_503_raises_service_unavailable' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L746 | `ASSERTION_THEATER` | Test 'test_eh7_connection_error_raises_service_unavailable' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L770 | `ASSERTION_THEATER` | Test 'test_hp3_get_forecast_accepts_verification_code_param' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L784 | `ASSERTION_THEATER` | Test 'test_hp3_get_forecast_accepts_capacity_kw_param' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| 🟡 WARN | `python/tests/test_freemium_forecast_client.py`:L797 | `ASSERTION_THEATER` | Test 'test_client_has_request_verification_code_method' has no substantive outcome value assertions (e.g. data contract keys, non-zero ranges, schema checks). Testing mocks without outcome checks is Mock Theater. |
| ... | *+ 39 more items in JSON report* | ... | ... |

## 5. DRY Invariants & Duplicative Functions

| Severity | File / Line | Rule | Details |
| :--- | :--- | :--- | :--- |
| 🟡 WARN | `backend/ooda_terminal_api/auth.py`:L122 | `DUPLICATE_FUNCTION_NAME` | Function 'authenticate' is duplicated across files (first defined in 'backend/inverter_telemetry_api/auth.py:L122'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/ooda_terminal_api/auth.py`:L122 | `DUPLICATE_FUNCTION_LOGIC` | Function 'authenticate' has identical AST code logic structure as 'authenticate' in 'backend/inverter_telemetry_api/auth.py:L122'. Refactor into shared module. |
| 🟡 WARN | `backend/ooda_terminal_api/db.py`:L225 | `DUPLICATE_FUNCTION_NAME` | Function 'get_data_period' is duplicated across files (first defined in 'backend/inverter_telemetry_api/db.py:L197'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/ooda_terminal_api/rate_limit.py`:L40 | `DUPLICATE_FUNCTION_NAME` | Function 'check_rate_limit' is duplicated across files (first defined in 'backend/inverter_telemetry_api/rate_limit.py:L34'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/ooda_terminal_api/validators.py`:L191 | `DUPLICATE_FUNCTION_NAME` | Function 'validate_site_params' is duplicated across files (first defined in 'backend/inverter_telemetry_api/validators.py:L191'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/ooda_terminal_api/validators.py`:L229 | `DUPLICATE_FUNCTION_NAME` | Function 'validate_data_period_params' is duplicated across files (first defined in 'backend/inverter_telemetry_api/validators.py:L229'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/docs/resource.py`:L334 | `DUPLICATE_FUNCTION_NAME` | Function 'class_name' is duplicated across files (first defined in 'backend/package/boto3/docs/base.py:L34'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/resources/factory.py`:L41 | `DUPLICATE_FUNCTION_NAME` | Function 'load_from_definition' is duplicated across files (first defined in 'backend/package/boto3/resources/collection.py:L377'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/s3/inject.py`:L80 | `DUPLICATE_FUNCTION_LOGIC` | Function 'inject_object_methods' has identical AST code logic structure as 'inject_s3_transfer_methods' in 'backend/package/boto3/s3/inject.py:L55'. Refactor into shared module. |
| 🟡 WARN | `backend/package/boto3/s3/inject.py`:L403 | `DUPLICATE_FUNCTION_NAME` | Function 'copy' is duplicated across files (first defined in 'backend/package/boto3/resources/base.py:L60'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/s3/transfer.py`:L430 | `DUPLICATE_FUNCTION_NAME` | Function 'upload_file' is duplicated across files (first defined in 'backend/package/boto3/s3/inject.py:L137'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/s3/transfer.py`:L462 | `DUPLICATE_FUNCTION_NAME` | Function 'download_file' is duplicated across files (first defined in 'backend/package/boto3/s3/inject.py:L185'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/session.py`:L233 | `DUPLICATE_FUNCTION_NAME` | Function 'client' is duplicated across files (first defined in 'backend/package/boto3/__init__.py:L87'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/boto3/session.py`:L341 | `DUPLICATE_FUNCTION_NAME` | Function 'resource' is duplicated across files (first defined in 'backend/package/boto3/__init__.py:L96'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/awsrequest.py`:L634 | `DUPLICATE_FUNCTION_NAME` | Function 'copy' is duplicated across files (first defined in 'backend/package/boto3/resources/base.py:L60'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/client.py`:L977 | `DUPLICATE_FUNCTION_NAME` | Function 'close' is duplicated across files (first defined in 'backend/package/botocore/awsrequest.py:L79'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/client.py`:L1320 | `DUPLICATE_FUNCTION_NAME` | Function 'get_waiter' is duplicated across files (first defined in 'backend/package/boto3/utils.py:L87'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/client.py`:L1408 | `DUPLICATE_FUNCTION_NAME` | Function 'region_name' is duplicated across files (first defined in 'backend/package/boto3/session.py:L123'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/compat.py`:L294 | `DUPLICATE_FUNCTION_NAME` | Function 'has_minimum_crt_version' is duplicated across files (first defined in 'backend/package/boto3/s3/transfer.py:L230'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/context.py`:L100 | `DUPLICATE_FUNCTION_NAME` | Function 'with_current_context' is duplicated across files (first defined in 'backend/package/boto3/s3/inject.py:L33'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/context.py`:L117 | `DUPLICATE_FUNCTION_NAME` | Function 'decorator' is duplicated across files (first defined in 'backend/package/boto3/s3/inject.py:L34'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/context.py`:L119 | `DUPLICATE_FUNCTION_NAME` | Function 'wrapper' is duplicated across files (first defined in 'backend/package/boto3/s3/inject.py:L36'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L272 | `DUPLICATE_FUNCTION_NAME` | Function 'get_credentials' is duplicated across files (first defined in 'backend/package/boto3/session.py:L211'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L486 | `DUPLICATE_FUNCTION_LOGIC` | Function 'secret_key' has identical AST code logic structure as 'access_key' in 'backend/package/botocore/credentials.py:L473'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L499 | `DUPLICATE_FUNCTION_LOGIC` | Function 'token' has identical AST code logic structure as 'access_key' in 'backend/package/botocore/credentials.py:L473'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L512 | `DUPLICATE_FUNCTION_LOGIC` | Function 'account_id' has identical AST code logic structure as 'access_key' in 'backend/package/botocore/credentials.py:L473'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1038 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1078 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1162 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1244 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1344 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1384 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1448 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1506 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1618 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1908 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L2084 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L2453 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L2741 | `DUPLICATE_FUNCTION_NAME` | Function 'load' is duplicated across files (first defined in 'backend/package/boto3/resources/model.py:L452'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/crt/auth.py`:L60 | `DUPLICATE_FUNCTION_NAME` | Function 'add_auth' is duplicated across files (first defined in 'backend/package/botocore/auth.py:L117'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/crt/auth.py`:L253 | `DUPLICATE_FUNCTION_NAME` | Function 'add_auth' is duplicated across files (first defined in 'backend/package/botocore/auth.py:L117'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/__init__.py`:L20 | `DUPLICATE_FUNCTION_NAME` | Function 'generate_docs' is duplicated across files (first defined in 'backend/package/boto3/docs/__init__.py:L20'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/docstringparser.py`:L34 | `DUPLICATE_FUNCTION_NAME` | Function 'reset' is duplicated across files (first defined in 'backend/package/boto3/dynamodb/conditions.py:L319'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/docstringparser.py`:L43 | `DUPLICATE_FUNCTION_NAME` | Function 'close' is duplicated across files (first defined in 'backend/package/botocore/awsrequest.py:L79'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/restdoc.py`:L66 | `DUPLICATE_FUNCTION_NAME` | Function 'write' is duplicated across files (first defined in 'backend/package/botocore/docs/bcdoc/docstringparser.py:L95'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/restdoc.py`:L110 | `DUPLICATE_FUNCTION_NAME` | Function 'handle_data' is duplicated across files (first defined in 'backend/package/botocore/docs/bcdoc/docstringparser.py:L55'). Share logic via central package import instead of repeating function definitions. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/style.py`:L205 | `DUPLICATE_FUNCTION_LOGIC` | Function 'end_important' has identical AST code logic structure as 'end_note' in 'backend/package/botocore/docs/bcdoc/style.py:L195'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/style.py`:L215 | `DUPLICATE_FUNCTION_LOGIC` | Function 'end_danger' has identical AST code logic structure as 'end_note' in 'backend/package/botocore/docs/bcdoc/style.py:L195'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/style.py`:L289 | `DUPLICATE_FUNCTION_LOGIC` | Function 'end_i' has identical AST code logic structure as 'end_b' in 'backend/package/botocore/docs/bcdoc/style.py:L124'. Refactor into shared module. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/style.py`:L320 | `DUPLICATE_FUNCTION_LOGIC` | Function 'start_ol' has identical AST code logic structure as 'start_ul' in 'backend/package/botocore/docs/bcdoc/style.py:L308'. Refactor into shared module. |
| ... | *+ 512 more items in JSON report* | ... | ... |

## 6. Architectural Naming & Contract Invariants

✅ *No issues found in this category.*

## 7. Error Handling & Exception Hygiene

| Severity | File / Line | Rule | Details |
| :--- | :--- | :--- | :--- |
| 🟡 WARN | `audit-code-integrity.py`:L341 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/boto3/docs/service.py`:L80 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/configprovider.py`:L622 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/credentials.py`:L1708 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/docs/bcdoc/style.py`:L96 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/docs/service.py`:L79 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/eventstream.py`:L616 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/handlers.py`:L809 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/handlers.py`:L1342 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/hooks.py`:L390 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/loaders.py`:L434 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/session.py`:L1160 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/session.py`:L1223 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/session.py`:L1230 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/session.py`:L460 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/session.py`:L1207 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L1008 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L3212 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L3226 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L967 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L3237 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/utils.py`:L2188 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/vendored/six.py`:L103 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/botocore/vendored/six.py`:L209 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/parser/_parser.py`:L325 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/parser/_parser.py`:L332 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/rrule.py`:L1320 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/rrule.py`:L861 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L149 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L961 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L966 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1187 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1748 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1597 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1613 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1642 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/dateutil/tz/tz.py`:L1666 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/jmespath/parser.py`:L85 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/__init__.py`:L363 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/crt.py`:L359 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/crt.py`:L1073 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/manager.py`:L759 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/tasks.py`:L215 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/s3transfer/utils.py`:L295 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/six.py`:L103 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/six.py`:L209 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/urllib3/__init__.py`:L28 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/urllib3/_collections.py`:L212 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/urllib3/connectionpool.py`:L1139 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| 🟡 WARN | `backend/package/urllib3/connectionpool.py`:L318 | `SWALLOWED_EXCEPTION` | Exception handler silently swallows errors with bare 'pass' without logging. |
| ... | *+ 17 more items in JSON report* | ... | ... |
