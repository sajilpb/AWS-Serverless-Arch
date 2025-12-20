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


# Dedicated bucket for SES inbound email storage
# module "s3_ses" {
#   source       = "./modules/S3"
#   s3bucketname = var.ses_bucket_name
# }

# # Amazon SES setup to store inbound emails to the SES bucket
# module "ses" {
#   source          = "./modules/ses"
#   domain          = local.my_domain
#   ses_bucket_name = var.ses_bucket_name
#   rule_set_name   = "inbound"

#   depends_on = [module.s3_ses]
# }

module "ACM" {
  source          = "./modules/acmcertificate"
  my_domain         = local.my_domain
}

module "Cognito" {
  source = "./modules/Cognito"
}