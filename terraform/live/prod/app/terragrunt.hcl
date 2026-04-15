include {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../"
}

inputs = {
  s3bucketname = "prod-froneendtwebsite2026"
  ses_bucket_name = "prod-froneendtwebsite2026ses"
  source_file_path = "${get_terragrunt_dir()}/../../../../Backend"
  output_zip_path = "./build/login_redirect.zip"
  cognito_domain_prefix = "prod-sajilclick"
  my_domain = "prod.sajil.click"
  certificate_domain = "sajil.click"
  route53_zone_name = "sajil.click"
  instancecreateworker = "prod-create-instance-worker"
  awsrolename          = "prodawsrole"
  loginredirect = "prodloginredirect"
  InstanceManagementTable = "prodInstanceManagementTable"
  loggroupname = "/aws/apigateway/http-api-access-prod"
  userpool = "prod-userpool"
  cognito-client = "prod-cognito-client"
  defaultoac = "prod-default-oac"
  tags = {
    Enviorment = "prod"
  }
}