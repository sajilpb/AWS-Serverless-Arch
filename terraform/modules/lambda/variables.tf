variable "source_file_path" {
  type = string
  description = "Path to the source lambda function"
}

variable "output_zip_path" {
  type = string
  description = "path to the zip file"
}

variable "runtime" {
  type = string
  default = "python3.11"
}

variable "Cognito_domain_prefix" {
  type = string
  description = "Cognito domain prefix"
}

variable "Cognito_client_id" {
  type = string
  description = "Cognito client ID"
}

variable "my_domain" {
  type = string
  description = "The domain name for the application"
}

variable "aws_apigatewayv2_api" {
  type = string
  description = "The API Gateway ARN for Lambda permission"
}

variable "Cognito_user_pool_id" {
  type        = string
  description = "Cognito User Pool ID"
}

variable "Cognito_client_secret" {
  type        = string
  description = "Cognito App Client secret (optional)"
  default     = ""
}

variable "oidc_scopes" {
  type        = string
  description = "OIDC scopes to request"
  default     = "email openid"
}