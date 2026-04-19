"""Base service client with common functionality."""

import json
import logging
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

from ..config import OnaConfig
from ..exceptions import ServiceUnavailableError, ResourceNotFoundError, ValidationError
from ..utils import retry_with_backoff

logger = logging.getLogger(__name__)


class BaseServiceClient:
    """Base class for all service clients.

    Provides common functionality for Lambda invocation, HTTP requests,
    and error handling.
    """

    def __init__(self, config: OnaConfig):
        """Initialize base service client.

        Args:
            config: SDK configuration
        """
        self.config = config
        self._lambda_client = None
        self._s3_client = None
        self._dynamodb = None

    @property
    def lambda_client(self):
        """Lazy-loaded Lambda client."""
        if self._lambda_client is None:
            self._lambda_client = boto3.client("lambda", region_name=self.config.aws_region)
        return self._lambda_client

    @property
    def s3_client(self):
        """Lazy-loaded S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self.config.aws_region)
        return self._s3_client

    @property
    def dynamodb(self):
        """Lazy-loaded DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource("dynamodb", region_name=self.config.aws_region)
        return self._dynamodb

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def invoke_lambda(
        self, function_name: str, payload: Dict[str, Any], invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """Invoke a Lambda function.

        Args:
            function_name: Name of the Lambda function
            payload: Request payload
            invocation_type: Type of invocation (RequestResponse or Event)

        Returns:
            Response from Lambda function

        Raises:
            ServiceUnavailableError: If Lambda invocation fails
            ValidationError: If response indicates validation error
            ResourceNotFoundError: If response indicates resource not found
        """
        try:
            logger.debug(f"Invoking Lambda function: {function_name}")
            logger.debug(f"Payload: {json.dumps(payload, default=str)}")

            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload),
            )

            if invocation_type == "Event":
                return {"status": "invoked"}

            payload_str = response["Payload"].read().decode("utf-8")
            result = json.loads(payload_str)

            logger.debug(f"Lambda response: {json.dumps(result, default=str)}")

            if "statusCode" in result:
                status_code = result["statusCode"]

                if status_code >= 500:
                    error_msg = result.get("body", {}).get("error", "Service error")
                    raise ServiceUnavailableError(f"Service error: {error_msg}")
                elif status_code == 404:
                    error_msg = result.get("body", {}).get("error", "Resource not found")
                    raise ResourceNotFoundError(error_msg)
                elif status_code == 400:
                    error_msg = result.get("body", {}).get("error", "Validation error")
                    raise ValidationError(error_msg)
                elif status_code >= 400:
                    error_msg = result.get("body", {}).get("error", "Request error")
                    raise ServiceUnavailableError(f"Request error: {error_msg}")

                if isinstance(result.get("body"), str):
                    result["body"] = json.loads(result["body"])

                return result.get("body", result)

            return result

        except ClientError as e:
            logger.error(f"Lambda invocation failed: {e}")
            raise ServiceUnavailableError(f"Lambda invocation failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Lambda response: {e}")
            raise ServiceUnavailableError(f"Invalid response from service: {e}")

    def get_s3_object(self, bucket: str, key: str) -> bytes:
        """Get an object from S3.

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            Object content as bytes

        Raises:
            ResourceNotFoundError: If object not found
            ServiceUnavailableError: If S3 operation fails
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise ResourceNotFoundError(f"Object not found: s3://{bucket}/{key}")
            raise ServiceUnavailableError(f"S3 operation failed: {e}")

    def put_s3_object(
        self, bucket: str, key: str, body: bytes, content_type: Optional[str] = None
    ) -> None:
        """Put an object to S3.

        Args:
            bucket: S3 bucket name
            key: Object key
            body: Object content
            content_type: Optional content type

        Raises:
            ServiceUnavailableError: If S3 operation fails
        """
        try:
            kwargs = {"Bucket": bucket, "Key": key, "Body": body}
            if content_type:
                kwargs["ContentType"] = content_type
            self.s3_client.put_object(**kwargs)
        except ClientError as e:
            raise ServiceUnavailableError(f"S3 operation failed: {e}")

    def list_s3_objects(self, bucket: str, prefix: str) -> list:
        """List objects in S3.

        Args:
            bucket: S3 bucket name
            prefix: Object prefix

        Returns:
            List of object keys

        Raises:
            ServiceUnavailableError: If S3 operation fails
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            raise ServiceUnavailableError(f"S3 operation failed: {e}")
