output "function_arn" {
  value = aws_lambda_function.login_redirect.arn
}

output "function_name" {
  value = aws_lambda_function.login_redirect.function_name
}

output "production_alias_invoke_arn" {
  value = aws_lambda_alias.production.invoke_arn
}
