variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "scango-receipt-intelligence"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for Nova"
  type        = string
  default     = "amazon.nova-pro-v1:0"  # TODO: Replace with actual Nova model ID
}

variable "create_s3_bucket" {
  description = "Whether to create S3 bucket for artifacts"
  type        = bool
  default     = false
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 30
}

variable "dynamodb_ttl_days" {
  description = "TTL for cached items in days"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "lambda_zip_path" {
  description = "Path to the Lambda function ZIP file"
  type        = string
  default     = "../lambda.zip"  # Relative to terraform directory
}