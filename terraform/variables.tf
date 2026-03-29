variable "s3bucketname" {
  default = "froneendtwebsite2026"
}

variable "ses_bucket_name" {
  description = "S3 bucket name used by SES to store inbound emails"
  default     = "froneendtwebsite2026ses"
  type = string
}

variable "source_file_path" {
  description = "Path to the Lambda source directory (zipped and deployed)"
  default     = "../Backend"
}

variable "output_zip_path" {
  description = "Output zip path for the packaged Lambda"
  default     = "./build/login_redirect.zip"
}

variable "cognito_domain_prefix" {
  description = "Globally unique domain prefix for Cognito Hosted UI"
  type        = string
  default     = "sajilclick"
}