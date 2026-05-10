resource "aws_cloudwatch_metric_alarm" "lambda_error_rate" {
  alarm_name                = "Lambda-error-rate"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = 1
  threshold                 = 1
  alarm_description         = "Request error rate has exceeded 10%"
  insufficient_data_actions = []

  metric_query {
    id = "m1"
    return_data = false

    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 60
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        FunctionName = var.lambda_function_name
        Resource     = "${var.lambda_function_name}:production"
      }
    }
  }

  metric_query {
    id = "m2"
    return_data = false

    metric {
      metric_name = "Throttles"
      namespace   = "AWS/Lambda"
      period      = 60
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        FunctionName = var.lambda_function_name
        Resource     = "${var.lambda_function_name}:production"
      }
    }
  }

  metric_query {
    id = "e1"
    expression = "m1 + m2"
    label = "Lambda errors plus throttle"
    return_data = true
  }
}