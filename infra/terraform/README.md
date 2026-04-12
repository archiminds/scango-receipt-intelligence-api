# ScanGo Receipt Intelligence – Terraform Stack

Provision the minimal AWS footprint for the serverless receipt parsing API: HTTP API Gateway → Lambda → DynamoDB cache with Amazon Bedrock Nova access plus optional S3 artifact storage.

## Prerequisites
- Terraform >= 1.5
- AWS account with Bedrock Nova access already approved in your target region
- Configured AWS credentials on this machine (`aws configure`, SSO, or environment variables)
- Packaged Lambda source zip (see below)

## Files in this folder
| File | Purpose |
| --- | --- |
| `versions.tf` / `provider.tf` | Terraform + AWS provider configuration |
| `locals.tf` | Centralized naming/tag conventions |
| `variables.tf` | Input variables (see `terraform.tfvars.example`) |
| `dynamodb.tf` | DynamoDB cache with TTL |
| `lambda.tf` | Lambda function + log group |
| `iam.tf` | IAM role and policies (logs, DynamoDB, Bedrock, optional S3) |
| `apigateway.tf` | HTTP API, stage, route, and Lambda permissions |
| `s3.tf` | Optional artifact bucket (controlled via `enable_s3`) |
| `outputs.tf` | Key deployment outputs |
| `terraform.tfvars.example` | Sample variable values |

## Packaging the Lambda
From the repo root:

```bash
mkdir -p dist
python -m zipfile -c dist/receipt_lambda.zip app/
# or use `zip -r dist/receipt_lambda.zip app -x "__pycache__/*"` once dependencies are vendored
```

Update `lambda_zip_path` in your `terraform.tfvars` to point at the generated ZIP (relative paths are resolved from this `infra/terraform` directory).

## Required variables
Set via `terraform.tfvars`, environment variables, or CLI flags:

- `aws_region`
- `project_name`
- `environment`
- `lambda_zip_path`
- `bedrock_model_id`
- `lambda_function_name` (optional override)
- `dynamodb_table_name` (optional override)
- `enable_s3` and `s3_bucket_name` (when S3 storage is desired)
- `tags` (map) for ownership/compliance metadata

Copy `terraform.tfvars.example` to `terraform.tfvars` and edit the values:

```bash
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars
```

## Deploy steps
```bash
cd infra/terraform
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Use `-var-file` if you maintain multiple environment configs.

## Testing the deployed API
After apply, capture the outputs (or run `terraform output`). Invoke the API with curl:

```bash
API_URL=$(terraform output -raw api_invoke_url)
curl -X POST "$API_URL/v1/receipts/parse" \
  -H "Content-Type: application/json" \
  -d '{
        "receipt_text": "STARBUCKS\nTotal: $5.50\nGST: $0.50",
        "currency": "AUD"
      }'
```

Expect a structured JSON response produced by the Lambda/Bedrock flow. CloudWatch log groups for both the Lambda and API stage are created automatically.

## Notes & Assumptions
- Bedrock Nova access must already be enabled for the account + region (Terraform only grants Lambda permissions to call it).
- No AWS credentials, `.env`, `.tfstate`, or zips are committed—verify `git status` before pushing.
- S3 bucket creation is optional; set `enable_s3 = false` to skip, or provide a globally-unique `s3_bucket_name` when enabled.
- The Lambda IAM policy grants DynamoDB (Get/Put/Update/Query), CloudWatch Logs, and Bedrock `InvokeModel`; expand it if additional AWS integrations are introduced later.
