locals {
  base_name   = "${var.project_name}-${var.environment}"
  lambda_name = coalesce(var.lambda_function_name, "${local.base_name}-lambda")
  dynamodb_table_name = coalesce(
    var.dynamodb_table_name,
    "${local.base_name}-cache"
  )

  api_name       = "${local.base_name}-http-api"
  api_stage_name = var.api_stage_name

  lambda_log_group_name = "/aws/lambda/${local.lambda_name}"
  api_log_group_name    = "/aws/apigateway/${local.api_name}"

  s3_bucket_name = var.enable_s3 ? coalesce(var.s3_bucket_name, "${local.base_name}-artifacts") : null

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
    },
    var.tags
  )
}
