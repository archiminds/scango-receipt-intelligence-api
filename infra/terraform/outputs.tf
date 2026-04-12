output "api_invoke_url" {
  description = "Invoke URL for the HTTP API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_function_name" {
  description = "Deployed Lambda function name"
  value       = aws_lambda_function.receipt.function_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table storing cached receipts"
  value       = aws_dynamodb_table.receipt_cache.name
}

output "artifacts_bucket_name" {
  description = "Optional S3 bucket for artifacts (null when disabled)"
  value       = var.enable_s3 ? aws_s3_bucket.artifacts[0].bucket : null
}

output "lambda_role_name" {
  description = "IAM role assumed by the Lambda function"
  value       = aws_iam_role.lambda.name
}
