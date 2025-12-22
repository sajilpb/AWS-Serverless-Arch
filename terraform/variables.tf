variable "s3bucketname" {
  default = "froneendtwebsite2026"
}

variable "ses_bucket_name" {
  description = "S3 bucket name used by SES to store inbound emails"
  default     = "froneendtwebsite2026ses"
  type = string
}

variable "source_file_path" {
  # Path to Backend login redirect Lambda source
    # Use a plain relative path; variables/functions aren't allowed in defaults
    default = "../Backend/login_redirect.py"
}

variable "output_zip_path" {
  # Output zip path for the packaged Lambda
    # Use a plain relative path for the zip output
    default = "../Backend/login_redirect.zip"
}

variable "cognito_domain_prefix" {
  description = "Globally unique domain prefix for Cognito Hosted UI"
  type        = string
  default     = "sajilclick"
}