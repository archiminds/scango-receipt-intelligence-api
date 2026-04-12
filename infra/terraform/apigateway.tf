resource "aws_apigatewayv2_api" "http" {
  name          = local.api_name
  protocol_type = "HTTP"
  description   = "ScanGo receipt parsing API"
  tags          = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  payload_format_version = "2.0"
  integration_uri        = aws_lambda_function.receipt.invoke_arn
}

resource "aws_apigatewayv2_route" "parse" {
  api_id             = aws_apigatewayv2_api.http.id
  route_key          = "POST /v1/receipts/parse"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "AWS_IAM"
}

resource "aws_cloudwatch_log_group" "api" {
  name              = local.api_log_group_name
  retention_in_days = var.log_retention_in_days
  tags              = local.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = local.api_stage_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      requestTime      = "$context.requestTime"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  default_route_settings {
    throttling_burst_limit = 1000
    throttling_rate_limit  = 500.0
  }
}

resource "aws_lambda_permission" "apigateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
