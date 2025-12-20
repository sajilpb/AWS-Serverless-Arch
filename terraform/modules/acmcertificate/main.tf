data "aws_acm_certificate" "amazon_issued" {
  domain      = var.my_domain
  types       = ["AMAZON_ISSUED"]
  most_recent = true
}