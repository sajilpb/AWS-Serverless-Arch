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

resource "aws_apigatewayv2_route" "create_ec2" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /create-ec2"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_route" "delete_instance" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "DELETE /instances/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.http_api_access.arn
    format = jsonencode({
      requestId      = "$context.requestId",
      routeKey       = "$context.routeKey",
      status         = "$context.status",
      integrationStatus = "$context.integrationStatus",
      authorizerError = "$context.authorizer.error",
      identity       = {
        sourceIp = "$context.identity.sourceIp",
        userAgent = "$context.identity.userAgent"
      },
      path           = "$context.path",
      method         = "$context.httpMethod"
    })
  }
}

resource "aws_cloudwatch_log_group" "http_api_access" {
  name              = "/aws/apigateway/http-api-access"
  retention_in_days = 7
}