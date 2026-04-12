output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.receipt_api.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.receipt_parser.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.receipt_parser.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for caching"
  value       = aws_dynamodb_table.receipt_cache.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.receipt_cache.arn
}

output "s3_bucket_name" {
  description = "S3 bucket name for artifacts (if created)"
  value       = var.create_s3_bucket ? aws_s3_bucket.artifacts[0].bucket : null
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN (if created)"
  value       = var.create_s3_bucket ? aws_s3_bucket.artifacts[0].arn : null
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    api   = aws_cloudwatch_log_group.api_logs.name
    lambda = aws_cloudwatch_log_group.lambda_logs.name
  }
}

output "iam_role_arn" {
  description = "IAM role ARN for Lambda"
  value       = aws_iam_role.lambda_role.arn
}