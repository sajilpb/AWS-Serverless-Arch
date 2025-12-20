variable "s3_origin_id" {
  description = "The S3 origin ID for CloudFront distribution"
  type        = string
}
variable "my_domain" {
  description = "The domain name for CloudFront distribution"
  type        = string
}
variable "aws_s3_bucket" {
  description = "The s3 bucket for frontend"
  type = string
}

variable "acm_certificate_arn" {
  description = "The SSL certificate ARN for CloudFront distribution"
  type        = string
}