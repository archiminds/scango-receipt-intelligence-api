terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "receipt_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  description   = "API for receipt parsing and intelligence"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.receipt_api.id
  name        = "prod"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp               = "$context.identity.sourceIp"
      requestTime            = "$context.requestTime"
      protocol               = "$context.protocol"
      httpMethod             = "$context.httpMethod"
      resourcePath           = "$context.resourcePath"
      routeKey               = "$context.routeKey"
      status                 = "$context.status"
      responseLength         = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

# Lambda Function
resource "aws_lambda_function" "receipt_parser" {
  function_name = "${var.project_name}-parser"
  runtime       = "python3.11"
  handler       = "app.api.handler.lambda_handler"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Reference external ZIP file (created separately)
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      DYNAMODB_TABLE_NAME  = aws_dynamodb_table.receipt_cache.name
      LOG_LEVEL           = "INFO"
      CACHE_TTL_DAYS      = tostring(var.dynamodb_ttl_days)
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_policy]
}

# API Gateway Integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.receipt_api.id
  integration_type = "AWS_PROXY"

  connection_type    = "INTERNET"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.receipt_parser.invoke_arn
}

resource "aws_apigatewayv2_route" "parse_route" {
  api_id    = aws_apigatewayv2_api.receipt_api.id
  route_key = "POST /v1/receipts/parse"

  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt_parser.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.receipt_api.execution_arn}/*/*"
}

# DynamoDB Table for Caching
resource "aws_dynamodb_table" "receipt_cache" {
  name         = "${var.project_name}-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "hash_key"

  attribute {
    name = "hash_key"
    type = "S"
  }

  attribute {
    name = "ttl"
    type = "N"
  }

  # TTL Configuration
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.project_name}-cache"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.receipt_cache.arn
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:*::foundation-model/${var.bedrock_model_id}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = var.create_s3_bucket ? "${aws_s3_bucket.artifacts[0].arn}/*" : "arn:aws:s3:::*/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_name}-api"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-parser"
  retention_in_days = var.log_retention_days
}

# Optional S3 Bucket for artifacts
resource "aws_s3_bucket" "artifacts" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = "${var.project_name}-artifacts-${random_string.bucket_suffix[0].result}"
}

resource "random_string" "bucket_suffix" {
  count   = var.create_s3_bucket ? 1 : 0
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

resource "aws_s3_bucket_versioning" "artifacts" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.artifacts[0].id
  versioning_configuration {
    status = "Enabled"
  }
}