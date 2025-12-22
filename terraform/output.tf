output "api_base_url" {
  description = "Base URL for the HTTP API"
  value       = module.apigateway.api_endpoint
}
