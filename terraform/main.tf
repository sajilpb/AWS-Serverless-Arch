module "cloudfront" {
  source        = "./modules/cloudfront"
  s3_origin_id  = local.s3_origin_id
  my_domain     = var.my_domain
  route53_zone_name = var.route53_zone_name
  acm_certificate_arn = module.ACM.acm_certificate_arn
  aws_s3_bucket = var.s3bucketname
  defaultoac = var.defaultoac
  tags = var.tags
  depends_on = [ module.s3 ]
  
}

module "s3" {
  source           = "./modules/S3"
  s3bucketname     = var.s3bucketname
  tags             = var.tags
  
}

module "s3_lambda" {
  source          = "./modules/S3"
  s3bucketname    = var.s3bucketnames3lambda
  source_file_path = var.source_file_path
  output_zip_path  = var.output_zip_path
  s3_key          = "login_redirect.py"
  tags = var.tags
}

module "ACM" {
  source          = "./modules/acmcertificate"
  certificate_domain         = var.certificate_domain
}

module "Cognito" {
  source = "./modules/Cognito"
  callback_url = "https://${var.my_domain}/index.html"
  domain_prefix = var.cognito_domain_prefix
  cognito-client = var.cognito-client
  userpool = var.userpool
}

module "lambda" {
  source                = "./modules/lambda"
  source_file_path      = var.source_file_path
  output_zip_path       = var.output_zip_path
  Cognito_domain_prefix = module.Cognito.domain_prefix
  Cognito_client_id     = module.Cognito.client_id
  Cognito_user_pool_id  = module.Cognito.user_pool_id
  s3bucketname          = module.s3_lambda.bucket_name
  s3_key                = module.s3_lambda.s3_key
  Cognito_client_secret = ""
  oidc_scopes           = "email openid"
  my_domain             = var.my_domain
  aws_apigatewayv2_api  = module.apigateway.api_gateway_arn
  dynamodb_table_name   = module.Dynamodb.instance_table_name
  awsiamrolename        = var.awsrolename
  loginredirect         = var.loginredirect
  InstanceManagementTable = var.InstanceManagementTable
  sourcecodehash        = module.s3_lambda.etag
  tags = var.tags
}

module "apigateway" {
  source       = "./modules/apigateway"
  # aws_lambda_login_redirect = module.lambda.function_arn
  aws_lambda_login_redirect = module.lambda.production_alias_invoke_arn
  loggroupname = var.loggroupname
}

module "Dynamodb" {
  source = "./modules/Dynamodb"
  InstanceManagementTable = var.InstanceManagementTable
  tags = var.tags
}

module "worker_lambda" {
  source              = "./modules/worker_lambda"
  source_file_path    = var.source_file_path
  output_zip_path     = "./build/instance_create_worker.zip"
  function_name       = var.instancecreateworker
  handler             = "hexapp.inbound.eventbridge_worker.lambda_handler"
  runtime             = "python3.11"
  dynamodb_table_name = module.Dynamodb.instance_table_name
  my_domain           = var.my_domain
}

module "Codebuild" {
  source = "./modules/Codepipelines"
  Codebuild-project-name = var.codebuildprojectname
  Codebuild-project-name-description = "var.codebuildprojectdescription"
  Source-repo = var.sourcerepo
  source-buildspec-file = var.buildspecfile
  source-branch = var.sourcebranch
  lambdafunctionname = module.lambda.function_name
  lambda_deployment_alarm_names = module.cloudwatch.lambda_deployment_alarm_names
}

module "cloudwatch" {
  source = "./modules/cloudwatch"
  lambda_function_name = module.lambda.function_name
}

resource "aws_cloudwatch_event_rule" "instance_create_requested" {
  name        = "instance-create-requested"
  description = "Routes InstanceCreateRequested events to the provisioning worker"

  event_pattern = jsonencode({
    source      = ["app.ec2-control-plane"],
    "detail-type" = ["InstanceCreateRequested", "InstancesTerminateRequested"]
  })
}

resource "aws_cloudwatch_event_target" "instance_create_worker" {
  rule = aws_cloudwatch_event_rule.instance_create_requested.name
  arn  = module.worker_lambda.function_arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke_worker" {
  statement_id  = "AllowEventBridgeInvokeWorker"
  action        = "lambda:InvokeFunction"
  function_name = module.worker_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.instance_create_requested.arn
}