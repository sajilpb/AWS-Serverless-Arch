output "api_gateway_arn" {
	description = "Execution ARN for the HTTP API"
	value       = aws_apigatewayv2_api.http_api.execution_arn
}

output "api_endpoint" {
	description = "Base URL for the HTTP API"
	value       = aws_apigatewayv2_api.http_api.api_endpoint
}
