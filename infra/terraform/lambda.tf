locals {
  lambda_environment_variables = merge(
    {
      DYNAMODB_TABLE_NAME = local.dynamodb_table_name
      BEDROCK_MODEL_ID    = var.bedrock_model_id
      LOG_GROUP_NAME      = local.lambda_log_group_name
    },
    var.enable_s3 && local.s3_bucket_name != null ? { S3_BUCKET_NAME = local.s3_bucket_name } : {},
    var.lambda_additional_environment
  )
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = local.lambda_log_group_name
  retention_in_days = var.log_retention_in_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "receipt" {
  function_name    = local.lambda_name
  description      = "Serverless receipt parsing for ${var.project_name}"
  role             = aws_iam_role.lambda.arn
  filename         = var.lambda_zip_path
  handler          = "app.api.handler.lambda_handler"
  runtime          = "python3.11"
  architectures    = var.lambda_architectures
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = local.lambda_environment_variables
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_inline
  ]

  tags = local.common_tags
}
