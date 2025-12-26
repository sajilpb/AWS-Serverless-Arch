module "cloudfront" {
  source        = "./modules/cloudfront"
  s3_origin_id  = local.s3_origin_id
  my_domain     = local.my_domain
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
  my_domain         = local.my_domain
}

module "Cognito" {
  source = "./modules/Cognito"
  callback_url = "https://${local.my_domain}/index.html"
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
  my_domain             = local.my_domain
  aws_apigatewayv2_api  = module.apigateway.api_gateway_arn
}

module "apigateway" {
  source       = "./modules/apigateway"
  aws_lambda_login_redirect = module.lambda.function_arn
}

module "Dynamodb" {
  source = "./modules/Dynamodb"
}