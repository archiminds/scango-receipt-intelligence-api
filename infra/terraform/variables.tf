variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Optional AWS CLI/SDK profile to use (falls back to default chain when null)"
  type        = string
  default     = null
}

variable "project_name" {
  description = "Human-readable project name used for tagging"
  type        = string
  default     = "scango-receipt-intelligence-api"
}

variable "environment" {
  description = "Deployment environment identifier (dev, staging, prod, etc.)"
  type        = string
  default     = "dev"
}

variable "lambda_function_name" {
  description = "Override for the Lambda function name (defaults to <project>-<env>-lambda when null)"
  type        = string
  default     = null
}

variable "lambda_zip_path" {
  description = "Relative or absolute path to the pre-built Lambda deployment ZIP"
  type        = string
}

variable "lambda_memory_size" {
  description = "Memory size in MB for the Lambda function"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout in seconds for the Lambda function"
  type        = number
  default     = 30
}

variable "lambda_additional_environment" {
  description = "Optional extra environment variables to merge into the Lambda configuration"
  type        = map(string)
  default     = {}
}

variable "dynamodb_table_name" {
  description = "Override for the DynamoDB table name (defaults to <project>-<env>-cache when null)"
  type        = string
  default     = null
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model identifier (for example amazon.nova-pro-v1:0)"
  type        = string
}

variable "enable_s3" {
  description = "Whether to provision an S3 bucket for artifacts/synthetic outputs"
  type        = bool
  default     = false
}

variable "s3_bucket_name" {
  description = "Optional explicit S3 bucket name when enable_s3 is true"
  type        = string
  default     = null
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "log_retention_in_days" {
  description = "Number of days to retain CloudWatch Logs"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Additional tags to apply to all supported resources"
  type        = map(string)
  default     = {}
}
