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

resource "aws_iam_role" "worker" {
  name               = "${var.function_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "archive_file" "worker" {
  type       = "zip"
  source_dir = var.source_file_path
  output_path = var.output_zip_path
}

resource "aws_lambda_function" "worker" {
  filename         = data.archive_file.worker.output_path
  function_name    = var.function_name
  role             = aws_iam_role.worker.arn
  handler          = var.handler
  source_code_hash = data.archive_file.worker.output_base64sha256
  timeout          = 300

  runtime = var.runtime

  environment {
    variables = {
      # Cognito variables aren't needed for the worker, but Settings.from_env tolerates empty values.
      COGNITO_DOMAIN_PREFIX = var.Cognito_domain_prefix
      COGNITO_CLIENT_ID     = var.Cognito_client_id
      COGNITO_REDIRECT_URI  = "https://${var.my_domain}/index.html"
      OIDC_SCOPES           = var.oidc_scopes
      DDB_TABLE_NAME        = var.dynamodb_table_name
    }
  }
}

data "aws_iam_policy_document" "worker_access" {
  statement {
    sid     = "WorkerAccess"
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
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_policy" {
  name   = "${var.function_name}-access"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_access.json
}
