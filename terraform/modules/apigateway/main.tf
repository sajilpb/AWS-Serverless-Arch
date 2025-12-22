# HTTP API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "serverless-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_headers = ["content-type", "authorization"]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
  }
}

resource "aws_apigatewayv2_integration" "login" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.aws_lambda_login_redirect
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "login" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /login"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_route" "logout" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /logout"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}