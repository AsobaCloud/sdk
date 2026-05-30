import json
from unittest.mock import MagicMock, patch
from partner_api.lambda_handler import lambda_handler

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
    from botocore.exceptions import ClientError
    mock_s3.get_object.side_effect = ClientError(
        {"Error": {"Code": "304", "Message": "Not Modified"}},
        "GetObject"
    )
    
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
