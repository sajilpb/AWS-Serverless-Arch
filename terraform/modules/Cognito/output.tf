output "user_pool_id" {
	value = aws_cognito_user_pool.pool.id
}

output "user_pool_client_id" {
	value = aws_cognito_user_pool_client.client.id
}

output "domain_prefix" {
	value = aws_cognito_user_pool_domain.cognito-domain.domain
}

output "client_id" {
	description = "Alias for Cognito user pool client id"
	value       = aws_cognito_user_pool_client.client.id
}
