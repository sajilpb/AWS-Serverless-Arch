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
  timeout       = 300

  runtime = var.runtime

    environment {
    variables = {
        COGNITO_DOMAIN_PREFIX = var.Cognito_domain_prefix
        COGNITO_CLIENT_ID     = var.Cognito_client_id
        COGNITO_REDIRECT_URI  = "https://${var.my_domain}/index.html"
        COGNITO_USER_POOL_ID  = var.Cognito_user_pool_id
        COGNITO_CLIENT_SECRET = var.Cognito_client_secret
        OIDC_SCOPES           = var.oidc_scopes
        DDB_TABLE_NAME        = var.dynamodb_table_name
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

resource "aws_lambda_permission" "apigw_create_ec2" {
  statement_id  = "AllowInvokeFromHttpApiCreateEc2"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_redirect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.aws_apigatewayv2_api}/*/POST/create-ec2"
}

resource "aws_lambda_permission" "apigw_delete_instance" {
  statement_id  = "AllowInvokeFromHttpApiDeleteInstance"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_redirect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.aws_apigatewayv2_api}/*/DELETE/instances/*"
}

resource "aws_lambda_permission" "apigw_delete_instances_all" {
  statement_id  = "AllowInvokeFromHttpApiDeleteInstancesAll"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_redirect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.aws_apigatewayv2_api}/*/DELETE/instances"
}

data "aws_iam_policy_document" "ec2_access" {
  statement {
    sid     = "EC2Access"
    effect  = "Allow"
    actions = [
      "ec2:RunInstances",
      "ec2:DescribeImages",
      "ec2:CreateTags",
      "ec2:TerminateInstances",
      "ec2:DescribeInstances",
      "ec2:DescribeVpcs",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_ec2_policy" {
  name   = "lambda-ec2-access"
  role   = aws_iam_role.example.id
  policy = data.aws_iam_policy_document.ec2_access.json
}