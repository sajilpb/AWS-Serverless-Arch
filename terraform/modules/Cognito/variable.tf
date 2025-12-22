variable "callback_url" {
	description = "Callback URL for Cognito Hosted UI (e.g., https://app.example.com/index.html)"
	type        = string
}

variable "domain_prefix" {
	description = "Globally unique domain prefix for Cognito Hosted UI"
	type        = string
}
