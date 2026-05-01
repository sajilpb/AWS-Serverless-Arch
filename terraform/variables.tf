variable "s3bucketname" {
}

variable "ses_bucket_name" {
  description = "S3 bucket name used by SES to store inbound emails"
  type = string
}

variable "source_file_path" {
  description = "Path to the Lambda source directory (zipped and deployed)"
}

variable "output_zip_path" {
  description = "Output zip path for the packaged Lambda"
}

variable "cognito_domain_prefix" {
  description = "Globally unique domain prefix for Cognito Hosted UI"
  type        = string
}

variable "my_domain" {
  type = string
}

variable "certificate_domain" {
  description = "Domain pattern used to look up ACM certificate (e.g. *.sajil.click)"
  type        = string
}

variable "route53_zone_name" {
  description = "Hosted zone name for DNS records (for example sajil.click)"
  type        = string
}

variable "instancecreateworker" {
  type        = string
}

variable "awsrolename" {
  type        = string
}

variable "loginredirect"{
  type = string
}

variable "InstanceManagementTable" {
  type = string
}

variable "loggroupname" {
  type = string
}

variable "cognito-client"{
  type = string
}

variable "userpool" {
  type = string
}

variable "defaultoac" {
  type = string
}

variable "tags" {
 type = map(string)  
}

variable "s3bucketnames3lambda" {
  type = string
}

variable "sourcecodehash" {
  type = string
}