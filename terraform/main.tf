module "cloudfront" {
  source        = "./modules/cloudfront"
  s3_origin_id  = local.s3_origin_id
  my_domain     = var.my_domain
  acm_certificate_arn = module.ACM.acm_certificate_arn
  aws_s3_bucket = var.s3bucketname
  depends_on = [ module.s3 ]
}

module "s3" {
  source          = "./modules/S3"
  s3bucketname    = var.s3bucketname
}

module "ACM" {
  source          = "./modules/acmcertificate"
  certificate_domain         = var.certificate_domain
}

module "Cognito" {
  source = "./modules/Cognito"
  callback_url = "https://${var.my_domain}/index.html"
  domain_prefix = var.cognito_domain_prefix
}

module "lambda" {
  source                = "./modules/lambda"
  source_file_path      = var.source_file_path
  output_zip_path       = var.output_zip_path
  Cognito_domain_prefix = module.Cognito.domain_prefix
  Cognito_client_id     = module.Cognito.client_id
  Cognito_user_pool_id  = module.Cognito.user_pool_id
  Cognito_client_secret = ""
  oidc_scopes           = "email openid"
  my_domain             = var.my_domain
  aws_apigatewayv2_api  = module.apigateway.api_gateway_arn
  dynamodb_table_name   = module.Dynamodb.instance_table_name
}

module "apigateway" {
  source       = "./modules/apigateway"
  aws_lambda_login_redirect = module.lambda.function_arn
}

module "Dynamodb" {
  source = "./modules/Dynamodb"
}

module "worker_lambda" {
  source              = "./modules/worker_lambda"
  source_file_path    = var.source_file_path
  output_zip_path     = "./build/instance_create_worker.zip"
  function_name       = "instance-create-worker"
  handler             = "hexapp.inbound.eventbridge_worker.lambda_handler"
  runtime             = "python3.11"
  dynamodb_table_name = module.Dynamodb.instance_table_name
  my_domain           = var.my_domain
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