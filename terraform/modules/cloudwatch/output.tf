output "lambda_deployment_alarm_names" {
  value = [aws_cloudwatch_metric_alarm.lambda_error_rate.alarm_name]
}

output "metric_name" {
  value = [aws_cloudwatch_metric_alarm.lambda_error_rate.alarm_name]
}