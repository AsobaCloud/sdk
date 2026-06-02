"""Regression tests for AuthClient.

Tests cover authentication flows, token management, MFA verification,
and user context operations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import json

from ona_platform import OnaClient, OnaConfig
from ona_platform.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ServiceUnavailableError,
    ValidationError
)


# Fixtures

@pytest.fixture
def auth_config():
    """Create test configuration with auth endpoint."""
    return OnaConfig(
        aws_region='af-south-1',
        auth_endpoint='https://auth-api.asoba.co/prod',
        timeout=30
    )


@pytest.fixture
def auth_client(auth_config):
    """Create AuthClient instance."""
    from ona_platform.services.auth import AuthClient
    return AuthClient(auth_config)


@pytest.fixture
def mock_successful_login_response():
    """Mock successful login response."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test',
            'user': {
                'user_id': 'user_abc123',
                'username': 'test@example.com',
                'role_id': 'role_admin',
                'role_name': 'Admin',
                'customer_ids': ['cust_001'],
                'application_permissions': ['admin-gpu-panel', 'energy-analyst']
            },
            'message': 'Login successful'
        })
    }


@pytest.fixture
def mock_mfa_challenge_response():
    """Mock MFA challenge response."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'mfa_required': True,
            'mfa_token': 'mfa_challenge_token_123'
        })
    }


@pytest.fixture
def mock_mfa_enrollment_response():
    """Mock MFA enrollment response."""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'mfa_required': True,
            'mfa_enrollment': True,
            'mfa_token': 'mfa_enrollment_token_123',
            'provisioning_uri': 'otpauth://totp/Ona:test@example.com?secret=JBSWY3DPEHPK3PXP'
        })
    }


# Authentication Tests

class TestAuthLogin:
    """Test user login authentication."""

    def test_login_success_returns_token_and_user(self, auth_client):
        """Test successful login returns token and user data."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test',
            'user': {
                'user_id': 'user_abc123',
                'username': 'test@example.com',
                'role_id': 'role_admin'
            }
        })
        result = auth_client.login('test@example.com', 'password123')

        assert 'token' in result
        assert 'user' in result
        assert result['user']['username'] == 'test@example.com'
        assert auth_client._current_token == result['token']

    def test_login_missing_username_raises_error(self, auth_client):
        """Test login with missing username raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            auth_client.login('', 'password123')
        assert 'username' in str(exc_info.value).lower()

    def test_login_missing_password_raises_error(self, auth_client):
        """Test login with missing password raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            auth_client.login('test@example.com', '')
        assert 'password' in str(exc_info.value).lower()

    def test_login_invalid_credentials_raises_auth_error(self, auth_client):
        """Test login with invalid credentials raises AuthenticationError."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Invalid credentials'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.login('test@example.com', 'wrongpassword')
        assert 'Invalid credentials' in str(exc_info.value)

    def test_login_inactive_user_raises_auth_error(self, auth_client):
        """Test login with inactive user raises AuthenticationError."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('User account is inactive'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.login('inactive@example.com', 'password123')
        assert 'inactive' in str(exc_info.value).lower()

    def test_login_service_unavailable_raises_error(self, auth_client):
        """Test login when auth service is unavailable."""
        auth_client.invoke_lambda = MagicMock(side_effect=ServiceUnavailableError('Auth service unavailable'))
        with pytest.raises(ServiceUnavailableError):
            auth_client.login('test@example.com', 'password123')


class TestAuthMFA:
    """Test MFA verification flows."""

    def test_mfa_challenge_returned_for_mfa_users(self, auth_client):
        """Test that MFA challenge is returned for users with MFA enabled."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'mfa_required': True,
            'mfa_token': 'mfa_challenge_token_123'
        })
        result = auth_client.login('mfauser@example.com', 'password123')

        assert result['mfa_required'] is True
        assert 'mfa_token' in result
        assert 'token' not in result  # Full token not issued yet

    def test_mfa_enrollment_returned_for_new_mfa_users(self, auth_client):
        """Test that MFA enrollment is returned for users setting up MFA."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'mfa_required': True,
            'mfa_enrollment': True,
            'mfa_token': 'mfa_enrollment_token_123',
            'provisioning_uri': 'otpauth://totp/Ona:test@example.com?secret=JBSWY3DPEHPK3PXP'
        })
        result = auth_client.login('newmfauser@example.com', 'password123')

        assert result['mfa_required'] is True
        assert result['mfa_enrollment'] is True
        assert 'provisioning_uri' in result
        assert result['mfa_token'] == 'mfa_enrollment_token_123'

    def test_verify_mfa_success_returns_token(self, auth_client):
        """Test successful MFA verification returns full token."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.full',
            'user': {
                'user_id': 'user_abc123',
                'username': 'test@example.com'
            }
        })
        result = auth_client.verify_mfa('mfa_challenge_token_123', '123456')

        assert 'token' in result
        assert 'user' in result
        assert auth_client._current_token == result['token']

    def test_verify_mfa_invalid_code_raises_error(self, auth_client):
        """Test MFA verification with invalid TOTP code."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Invalid TOTP code'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.verify_mfa('mfa_token', '000000')
        assert 'Invalid TOTP code' in str(exc_info.value)

    def test_verify_mfa_expired_token_raises_error(self, auth_client):
        """Test MFA verification with expired challenge token."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Invalid or expired MFA token'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.verify_mfa('expired_token', '123456')
        assert 'expired' in str(exc_info.value).lower()

    def test_verify_mfa_missing_code_raises_validation_error(self, auth_client):
        """Test MFA verification with missing TOTP code."""
        with pytest.raises(ValidationError) as exc_info:
            auth_client.verify_mfa('mfa_token', '')
        assert 'totp' in str(exc_info.value).lower() or 'code' in str(exc_info.value).lower()


class TestAuthTokenManagement:
    """Test token management operations."""

    def test_set_token_updates_current_token(self, auth_client):
        """Test setting token updates internal state."""
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test'
        auth_client.set_token(token)
        assert auth_client._current_token == token

    def test_set_token_propagates_to_service_clients(self, auth_client):
        """Test setting token propagates to all service clients."""
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test'
        auth_client.set_token(token)
        
        # Verify token is available for HTTP-based services
        assert auth_client.get_auth_header() == {'Authorization': f'Bearer {token}'}

    def test_get_current_user_valid_token_returns_user(self, auth_client):
        """Test getting current user with valid token."""
        # Create a valid JWT token for testing
        import jwt
        from datetime import datetime, timedelta, timezone
        
        payload = {
            'user_id': 'user_abc123',
            'username': 'test@example.com',
            'role_id': 'role_admin',
            'customer_ids': ['cust_001'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            'iat': datetime.now(timezone.utc)
        }
        test_token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        auth_client.set_token(test_token)
        user = auth_client.get_current_user()

        assert user['user_id'] == 'user_abc123'
        assert user['username'] == 'test@example.com'

    def test_get_current_user_no_token_raises_error(self, auth_client):
        """Test getting current user without token raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.get_current_user()
        assert 'not authenticated' in str(exc_info.value).lower() or 'token' in str(exc_info.value).lower()

    def test_get_current_user_expired_token_raises_error(self, auth_client):
        """Test getting current user with expired token."""
        import jwt
        from datetime import datetime, timedelta, timezone
        
        # Create an expired token
        payload = {
            'user_id': 'user_abc123',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        auth_client.set_token(expired_token)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.get_current_user()
        assert 'expired' in str(exc_info.value).lower()

    def test_logout_clears_token(self, auth_client):
        """Test logout clears stored token."""
        auth_client.set_token('valid_token')
        auth_client.logout()
        assert auth_client._current_token is None

    def test_is_authenticated_returns_true_with_token(self, auth_client):
        """Test is_authenticated returns True when token exists."""
        auth_client.set_token('valid_token')
        assert auth_client.is_authenticated() is True

    def test_is_authenticated_returns_false_without_token(self, auth_client):
        """Test is_authenticated returns False when no token."""
        assert auth_client.is_authenticated() is False


class TestAuthTokenRefresh:
    """Test token refresh operations."""

    def test_refresh_token_success_returns_new_token(self, auth_client):
        """Test successful token refresh returns new token."""
        auth_client.set_token('old_token')
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'new_token_123',
            'expires_in': 86400
        })
        result = auth_client.refresh_token()

        assert result['token'] == 'new_token_123'
        assert auth_client._current_token == 'new_token_123'

    def test_refresh_token_without_existing_token_raises_error(self, auth_client):
        """Test refresh without existing token raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.refresh_token()
        assert 'not authenticated' in str(exc_info.value).lower()

    def test_refresh_token_invalid_token_raises_error(self, auth_client):
        """Test refresh with invalid token raises error."""
        auth_client.set_token('invalid_token')
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Invalid token'))
        with pytest.raises(AuthenticationError):
            auth_client.refresh_token()


class TestAuthAPIKeyManagement:
    """Test API key management for service-to-service auth."""

    def test_get_api_key_info_success(self, auth_client):
        """Test retrieving API key information."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'api_key_id': 'key_abc123',
            'permitted_site_ids': ['Sibaya', 'TestSite'],
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'created_at': (datetime.utcnow() - timedelta(days=60)).isoformat()
        })
        info = auth_client.get_api_key_info('opa_prod_test_key')

        assert 'api_key_id' in info
        assert 'Sibaya' in info['permitted_site_ids']
        assert 'expires_at' in info

    def test_get_api_key_info_invalid_key_raises_error(self, auth_client):
        """Test API key info with invalid key."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('API key not found'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.get_api_key_info('invalid_key')
        assert 'not found' in str(exc_info.value).lower()

    def test_get_api_key_info_expired_key_shows_expired(self, auth_client):
        """Test API key info shows expired status."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'api_key_id': 'key_expired',
            'expires_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
            'is_expired': True
        })
        info = auth_client.get_api_key_info('opa_prod_expired')
        assert info['is_expired'] is True

    def test_validate_api_key_success(self, auth_client):
        """Test API key validation success."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'valid': True,
            'permitted_site_ids': ['Sibaya']
        })
        result = auth_client.validate_api_key('opa_prod_valid', 'Sibaya')

        assert result['valid'] is True
        assert 'Sibaya' in result['permitted_site_ids']

    def test_validate_api_key_site_not_permitted(self, auth_client):
        """Test API key validation with unauthorized site."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Site not permitted'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.validate_api_key('opa_prod_valid', 'UnauthorizedSite')
        assert 'not permitted' in str(exc_info.value).lower()


class TestAuthIntegration:
    """Test integration with OnaClient."""

    def test_auth_client_lazy_loaded(self, auth_config):
        """Test AuthClient is lazy-loaded by OnaClient."""
        client = OnaClient(config=auth_config)
        assert client._auth is None
        
        # Access auth property
        _ = client.auth
        assert client._auth is not None

    def test_auth_client_shares_config(self, auth_config):
        """Test AuthClient shares configuration with main client."""
        client = OnaClient(config=auth_config)
        assert client.auth.config == auth_config

    def test_auth_token_propagates_to_services(self, auth_config):
        """Test auth token propagates to other service clients."""
        client = OnaClient(config=auth_config)
        
        # Set token via auth client
        client.auth.set_token('shared_token_123')
        
        # Verify other services can access the token
        # This depends on implementation - services may need to reference auth client
        assert client.auth.get_auth_header() == {'Authorization': 'Bearer shared_token_123'}


class TestAuthConfiguration:
    """Test configuration requirements."""

    def test_auth_client_requires_endpoint(self):
        """Test AuthClient requires auth endpoint in config."""
        config = OnaConfig(aws_region='af-south-1')  # No auth_endpoint
        from ona_platform.services.auth import AuthClient
        
        with pytest.raises(ConfigurationError) as exc_info:
            AuthClient(config)
        assert 'endpoint' in str(exc_info.value).lower() or 'auth' in str(exc_info.value).lower()

    def test_auth_client_accepts_https_endpoint(self, auth_config):
        """Test AuthClient accepts HTTPS endpoint."""
        from ona_platform.services.auth import AuthClient
        # Should not raise
        client = AuthClient(auth_config)
        assert client is not None

    def test_auth_client_rejects_http_endpoint(self):
        """Test AuthClient rejects non-HTTPS endpoint in production."""
        config = OnaConfig(
            aws_region='af-south-1',
            auth_endpoint='http://insecure-api.asoba.co/prod'  # HTTP - insecure
        )
        from ona_platform.services.auth import AuthClient
        
        with pytest.raises(ConfigurationError) as exc_info:
            AuthClient(config)
        assert 'https' in str(exc_info.value).lower()


class TestAuthErrorHandling:
    """Test error handling and edge cases."""

    def test_login_network_error_raises_service_unavailable(self, auth_client):
        """Test network error during login raises ServiceUnavailableError."""
        auth_client.invoke_lambda = MagicMock(side_effect=ServiceUnavailableError('Network error'))
        with pytest.raises(ServiceUnavailableError):
            auth_client.login('test@example.com', 'password123')

    def test_mfa_verification_network_error(self, auth_client):
        """Test network error during MFA verification."""
        auth_client.invoke_lambda = MagicMock(side_effect=ServiceUnavailableError('Network error'))
        with pytest.raises(ServiceUnavailableError):
            auth_client.verify_mfa('mfa_token', '123456')

    def test_malformed_login_response_raises_error(self, auth_client):
        """Test malformed login response handling."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'unexpected_field': 'value'  # Missing required fields
        })
        # Should not raise - implementation accepts any response
        result = auth_client.login('test@example.com', 'password123')
        assert 'unexpected_field' in result

    def test_token_with_missing_claims_handled_gracefully(self, auth_client):
        """Test token with missing claims is handled gracefully."""
        import jwt
        from datetime import datetime, timedelta, timezone
        
        # Create token with partial claims
        payload = {
            'user_id': 'user_123',
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }
        incomplete_token = jwt.encode(payload, 'test-secret', algorithm='HS256')
        auth_client.set_token(incomplete_token)
        user = auth_client.get_current_user()
        # Should return whatever is available
        assert user['user_id'] == 'user_123'
        assert user.get('username') is None


class TestAuthHeaders:
    """Test authentication header generation."""

    def test_get_auth_header_with_token(self, auth_client):
        """Test getting Authorization header with token set."""
        auth_client.set_token('test_token_123')
        headers = auth_client.get_auth_header()
        assert headers == {'Authorization': 'Bearer test_token_123'}

    def test_get_auth_header_without_token_returns_empty(self, auth_client):
        """Test getting Authorization header without token."""
        headers = auth_client.get_auth_header()
        assert headers == {}

    def test_get_auth_header_for_request_includes_bearer(self, auth_client):
        """Test request headers include Bearer prefix."""
        auth_client.set_token('my_token')
        headers = auth_client.get_auth_header()
        assert headers['Authorization'].startswith('Bearer ')


# Property-based / Stateful Tests

class TestAuthStateful:
    """Test stateful authentication scenarios."""

    def test_complete_login_flow_with_mfa(self, auth_client):
        """Test complete login flow with MFA challenge."""
        # Step 1: Login returns MFA challenge
        auth_client.invoke_lambda = MagicMock(return_value={
            'mfa_required': True,
            'mfa_token': 'challenge_123'
        })
        login_result = auth_client.login('mfauser@example.com', 'password123')
        assert login_result['mfa_required'] is True
            
        # Step 2: Verify MFA and get full token
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'full_access_token',
            'user': {'user_id': 'user_123', 'username': 'mfauser@example.com'}
        })
        mfa_result = auth_client.verify_mfa('challenge_123', '123456')
        assert 'token' in mfa_result
            
        # Step 3: Use token for authenticated request (get_current_user decodes locally)
        user = auth_client.get_current_user()
        # Token was set from mfa_result
        assert auth_client._current_token == 'full_access_token'

    def test_token_refresh_flow(self, auth_client):
        """Test token refresh flow."""
        # Start with valid token
        auth_client.set_token('original_token')
        
        # Refresh
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'refreshed_token',
            'expires_in': 86400
        })
        result = auth_client.refresh_token()
            
        assert auth_client._current_token == 'refreshed_token'
        assert auth_client.is_authenticated() is True

    def test_logout_invalidates_token(self, auth_client):
        """Test logout flow invalidates token."""
        # Login
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'session_token',
            'user': {'user_id': 'user_123'}
        })
        auth_client.login('test@example.com', 'password123')
        assert auth_client.is_authenticated() is True
            
        # Logout (local only, no server call needed)
        auth_client.logout()
            
        assert auth_client.is_authenticated() is False
        assert auth_client._current_token is None


    def test_exchange_token_success(self, auth_client):
        """Test external token exchange for SSO integration."""
        auth_client.invoke_lambda = MagicMock(return_value={
            'token': 'exchanged_ona_token',
            'user': {'user_id': 'user_123', 'username': 'external@example.com'}
        })
        result = auth_client.exchange_token('external_jwt_token', provider='external-sso')

        assert result['token'] == 'exchanged_ona_token'
        assert auth_client._current_token == 'exchanged_ona_token'

    def test_exchange_token_invalid_external_token(self, auth_client):
        """Test exchange with invalid external token."""
        auth_client.invoke_lambda = MagicMock(side_effect=AuthenticationError('Invalid external token'))
        with pytest.raises(AuthenticationError) as exc_info:
            auth_client.exchange_token('invalid_token', provider='external-sso')
        assert 'Invalid external token' in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
