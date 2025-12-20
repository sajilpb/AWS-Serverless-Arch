variable "s3bucketname" {
  default = "froneendtwebsite2026"
}

variable "s3_extra_bucket_names" {
  description = "Additional S3 bucket names to create"
  type        = list(string)
  default     = []
}

variable "ses_bucket_name" {
  description = "S3 bucket name used by SES to store inbound emails"
  default     = "froneendtwebsite2026ses"
  type = string
}