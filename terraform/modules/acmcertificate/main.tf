data "aws_acm_certificate" "amazon_issued" {
  domain      = var.certificate_domain
  types       = ["AMAZON_ISSUED"]
  most_recent = true
}