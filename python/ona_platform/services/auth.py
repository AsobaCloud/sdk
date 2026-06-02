"""Authentication client for Ona Platform SDK.

Provides unified authentication management including JWT-based login,
MFA verification, token lifecycle management, and API key introspection.
"""

import json
import logging
from typing import Dict, Optional

from ..config import OnaConfig
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    ServiceUnavailableError,
    ValidationError
)
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class AuthClient(BaseServiceClient):
    """Client for authentication and authorization operations.

    Handles user login, MFA verification, token management, and
    API key introspection for both user-facing and service-to-service
    authentication patterns.

    Example:
        >>> from ona_platform import OnaClient
        >>> client = OnaClient(auth_endpoint='https://auth.asoba.co')
        >>>
        >>> # Login
        >>> result = client.auth.login('user@example.com', 'password')
        >>> if result.get('mfa_required'):
        >>>     # Handle MFA
        >>>     result = client.auth.verify_mfa(result['mfa_token'], '123456')
        >>>
        >>> # Get current user
        >>> user = client.auth.get_current_user()
        >>>
        >>> # Set token directly (for external integrations)
        >>> client.auth.set_token('eyJhbGciOiJIUzI1NiIs...')
    """

    def __init__(self, config: OnaConfig):
        """Initialize AuthClient.

        Args:
            config: SDK configuration with auth_endpoint

        Raises:
            ConfigurationError: If auth_endpoint is not configured
                              or does not use HTTPS
        """
        super().__init__(config)
        
        if not hasattr(config, 'auth_endpoint') or not config.auth_endpoint:
            raise ConfigurationError("auth_endpoint is required for AuthClient")
        
        if not config.auth_endpoint.startswith('https://'):
            raise ConfigurationError("auth_endpoint must use HTTPS")
        
        self._endpoint = config.auth_endpoint.rstrip('/')
        self._current_token: Optional[str] = None
        self._session = None
        
    def refresh_token(self) -> Dict:
        """Refresh current authentication token.

        Returns:
            Dict with new token and expires_in

        Raises:
            AuthenticationError: If not authenticated or refresh fails
        """
        if not self._current_token:
            raise AuthenticationError("Not authenticated. Cannot refresh token.")

        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/refresh',
                'headers': {
                    'Authorization': f'Bearer {self._current_token}'
                }
            }
            
            result = self.invoke_lambda(self._get_auth_function_name(), payload)
            
            if 'token' in result:
                self._current_token = result['token']
            
            return result
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError(f"Failed to refresh token: {e}")

    def login(self, username: str, password: str) -> Dict:
        """Authenticate user with username and password.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            Dict with either:
            - token and user data (if no MFA required)
            - mfa_required, mfa_token (if MFA verification needed)
            - mfa_required, mfa_enrollment, mfa_token, provisioning_uri
              (if first-time MFA setup)

        Raises:
            ValidationError: If username or password is empty
            AuthenticationError: If credentials are invalid or account inactive
            ServiceUnavailableError: If authentication service is unavailable
        """
        if not username:
            raise ValidationError("Username is required")
        if not password:
            raise ValidationError("Password is required")

        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/login',
                'body': json.dumps({'username': username, 'password': password})
            }
            
            result = self.invoke_lambda(self._get_auth_function_name(), payload)
            
            # Handle MFA challenge
            if result.get('mfa_required'):
                mfa_response = {
                    'mfa_required': True,
                    'mfa_token': result.get('mfa_token')
                }
                
                if result.get('mfa_enrollment'):
                    mfa_response['mfa_enrollment'] = True
                    mfa_response['provisioning_uri'] = result.get('provisioning_uri')
                
                return mfa_response
            
            # Store token on successful login
            if 'token' in result:
                self._current_token = result['token']
            
            return result
            
        except AuthenticationError:
            raise
        except ServiceUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise ServiceUnavailableError(f"Authentication failed: {e}")

    def verify_mfa(self, mfa_token: str, totp_code: str) -> Dict:
        """Verify MFA TOTP code and complete authentication.

        Args:
            mfa_token: MFA challenge token from login response
            totp_code: TOTP code from authenticator app

        Returns:
            Dict with token and user data on success

        Raises:
            ValidationError: If mfa_token or totp_code is empty
            AuthenticationError: If TOTP code is invalid or token expired
            ServiceUnavailableError: If verification service is unavailable
        """
        if not mfa_token:
            raise ValidationError("MFA token is required")
        if not totp_code:
            raise ValidationError("TOTP code is required")

        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/verify-mfa',
                'body': json.dumps({
                    'mfa_token': mfa_token,
                    'totp_code': totp_code
                })
            }
            
            result = self.invoke_lambda(self._get_auth_function_name(), payload)
            
            # Store token on successful MFA verification
            if 'token' in result:
                self._current_token = result['token']
            
            return result
            
        except AuthenticationError:
            raise
        except ServiceUnavailableError:
            raise
        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            raise ServiceUnavailableError(f"MFA verification failed: {e}")

    def set_token(self, token: str) -> None:
        """Set authentication token directly.

        Use this when integrating with external systems that exchange
        their own tokens for Ona Platform tokens.

        Args:
            token: JWT token from Ona Platform
        """
        self._current_token = token
        logger.debug("Authentication token set")

    def get_token(self) -> Optional[str]:
        """Get current authentication token.

        Returns:
            Current JWT token or None if not authenticated
        """
        return self._current_token

    def is_authenticated(self) -> bool:
        """Check if client has authentication token.

        Returns:
            True if token is set, False otherwise
        """
        return self._current_token is not None

    def logout(self) -> None:
        """Clear authentication token.

        Note: This only clears the local token. The server-side
        session may remain valid until token expiry.
        """
        self._current_token = None
        logger.debug("Authentication token cleared")

    def get_current_user(self) -> Dict:
        """Get current user information from token.

        Returns:
            Dict with user_id, username, role_id, customer_ids, etc.

        Raises:
            AuthenticationError: If not authenticated or token is invalid
        """
        if not self._current_token:
            raise AuthenticationError("Not authenticated. Please login or set token.")

        try:
            # Decode token locally to get user info
            import jwt
            from datetime import datetime, timezone
            
            # Try to decode without signature verification (just to get claims)
            # The expiry is still verified
            payload = jwt.decode(
                self._current_token,
                options={"verify_signature": False, "verify_exp": True}
            )
            
            return {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'role_id': payload.get('role_id'),
                'customer_ids': payload.get('customer_ids', []),
                'group_id': payload.get('group_id'),
                'skin_id': payload.get('skin_id')
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired. Please login again.")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise AuthenticationError(f"Failed to validate token: {e}")

    def _get_auth_function_name(self) -> str:
        """Get the Lambda function name for auth requests.
        
        Returns:
            Lambda function name with stage prefix
        """
        # Derive stage from endpoint URL or use 'prod' as default
        if 'staging' in self._endpoint:
            return 'ona-user-auth-staging'
        elif 'dev' in self._endpoint or 'localhost' in self._endpoint:
            return 'ona-user-auth-dev'
        return 'ona-user-auth-prod'

    def get_api_key_info(self, api_key: str) -> Dict:
        """Get information about an API key.

        Args:
            api_key: API key to introspect (e.g., 'opa_prod_xxxxx')

        Returns:
            Dict with api_key_id, permitted_site_ids, expires_at, etc.

        Raises:
            AuthenticationError: If API key is invalid
            ServiceUnavailableError: If lookup fails
        """
        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/api-key-info',
                'body': json.dumps({'api_key': api_key})
            }
            
            result = self.invoke_lambda(self._get_auth_function_name(), payload)
            
            # Add computed is_expired field
            if 'expires_at' in result:
                from datetime import datetime, timezone
                try:
                    expiry = datetime.fromisoformat(result['expires_at'])
                    if expiry.tzinfo is None:
                        expiry = expiry.replace(tzinfo=timezone.utc)
                    result['is_expired'] = datetime.now(timezone.utc) >= expiry
                except ValueError:
                    result['is_expired'] = True
            
            return result
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"API key info lookup failed: {e}")
            raise ServiceUnavailableError(f"Failed to get API key info: {e}")

    def validate_api_key(self, api_key: str, site_id: str) -> Dict:
        """Validate API key and check site authorization.

        Args:
            api_key: API key to validate
            site_id: Site ID to check authorization for

        Returns:
            Dict with valid, permitted_site_ids on success

        Raises:
            AuthenticationError: If API key is invalid or not authorized for site
        """
        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/validate-api-key',
                'body': json.dumps({
                    'api_key': api_key,
                    'site_id': site_id
                })
            }
            
            return self.invoke_lambda(self._get_auth_function_name(), payload)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            raise ServiceUnavailableError(f"Failed to validate API key: {e}")

    def get_auth_header(self) -> Dict[str, str]:
        """Get Authorization header for HTTP requests.

        Returns:
            Dict with Authorization header if token is set,
            empty dict otherwise
        """
        if self._current_token:
            return {'Authorization': f'Bearer {self._current_token}'}
        return {}

    def exchange_token(self, external_token: str, provider: str = 'external') -> Dict:
        """Exchange external system token for Ona Platform token.

        Use this for SSO integrations where an external system
        authenticates the user and needs to obtain an Ona token.

        Args:
            external_token: Token from external identity provider
            provider: External provider identifier (default: 'external')

        Returns:
            Dict with Ona Platform token and user data

        Raises:
            AuthenticationError: If external token is invalid
            ServiceUnavailableError: If exchange service is unavailable
        """
        try:
            payload = {
                'httpMethod': 'POST',
                'path': '/api/auth/exchange',
                'body': json.dumps({
                    'external_token': external_token,
                    'provider': provider
                })
            }
            
            result = self.invoke_lambda(self._get_auth_function_name(), payload)
            
            if 'token' in result:
                self._current_token = result['token']
            
            return result
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise ServiceUnavailableError(f"Token exchange failed: {e}")
