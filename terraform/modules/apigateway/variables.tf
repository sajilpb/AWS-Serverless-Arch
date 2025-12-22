variable "aws_lambda_login_redirect" {
  type        = string
  description = "Lambda function ARN for login redirect"
}

variable "api_name" {
  type    = string
  default = "serverless-http-api"
}

variable "route_key" {
  type    = string
  default = "GET /login"
}