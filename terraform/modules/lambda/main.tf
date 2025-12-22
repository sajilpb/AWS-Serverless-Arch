# IAM role for Lambda execution
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "example" {
  name               = "lambda_execution_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Package the Lambda function code
data "archive_file" "login_redirect" {
  type        = "zip"
  source_file = var.source_file_path
  output_path = var.output_zip_path
}

# Lambda function
resource "aws_lambda_function" "login_redirect" {
  filename      = data.archive_file.login_redirect.output_path
  function_name = "login-redirect"
  role          = aws_iam_role.example.arn
  handler       = "login_redirect.lambda_handler"
  source_code_hash = data.archive_file.login_redirect.output_base64sha256

  runtime = var.runtime

    environment {
    variables = {
        COGNITO_DOMAIN_PREFIX = var.Cognito_domain_prefix
        COGNITO_CLIENT_ID     = var.Cognito_client_id
        COGNITO_REDIRECT_URI  = "https://${var.my_domain}/index.html"
        COGNITO_USER_POOL_ID  = var.Cognito_user_pool_id
        COGNITO_CLIENT_SECRET = var.Cognito_client_secret
        OIDC_SCOPES           = var.oidc_scopes
    }
  }

  tags = {
    Environment = "production"
    Application = "example"
  }
}


resource "aws_lambda_permission" "apigw_login" {
  statement_id  = "AllowInvokeFromHttpApiLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_redirect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.aws_apigatewayv2_api}/*/GET/login"
}

resource "aws_lambda_permission" "apigw_logout" {
  statement_id  = "AllowInvokeFromHttpApiLogout"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_redirect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.aws_apigatewayv2_api}/*/GET/logout"
}