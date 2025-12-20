variable "domain" {
  description = "Domain to receive emails for (must be in Route53)"
  type        = string
}

variable "ses_bucket_name" {
  description = "S3 bucket name to store inbound emails"
  type        = string
}

variable "rule_set_name" {
  description = "SES receipt rule set name"
  type        = string
  default     = "inbound"
}

variable "recipients" {
  description = "List of recipients to match; use the domain to match all addresses at that domain."
  type        = list(string)
  default     = []
}

variable "object_key_prefix" {
  description = "S3 key prefix for stored emails"
  type        = string
  default     = "emails/"
}
