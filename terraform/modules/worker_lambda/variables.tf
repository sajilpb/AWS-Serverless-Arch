variable "source_file_path" {
  type        = string
  description = "Path to the Lambda source directory (zipped and deployed)"
}

variable "output_zip_path" {
  type        = string
  description = "Output zip path for the packaged Lambda"
}

variable "runtime" {
  type    = string
  default = "python3.11"
}

variable "function_name" {
  type        = string
  description = "Lambda function name"
}

variable "handler" {
  type        = string
  description = "Lambda handler (module.function)"
}

variable "dynamodb_table_name" {
  type        = string
  description = "DynamoDB table name for storing user EC2 instances and request tracking"
}

variable "Cognito_domain_prefix" {
  type        = string
  description = "(Unused by worker) Kept for parity; can be empty"
  default     = ""
}

variable "Cognito_client_id" {
  type        = string
  description = "(Unused by worker) Kept for parity; can be empty"
  default     = ""
}

variable "my_domain" {
  type        = string
  description = "(Unused by worker) Kept for parity; can be empty"
  default     = ""
}

variable "oidc_scopes" {
  type        = string
  description = "(Unused by worker) Kept for parity; can be empty"
  default     = "openid email"
}
