# ScanGo Receipt Intelligence API

A production-ready serverless API for parsing OCR-extracted receipt text into structured JSON using AWS Lambda, API Gateway, DynamoDB, and Amazon Bedrock Nova.

## Architecture

- **API Gateway**: HTTP API for REST endpoints
- **Lambda**: Serverless compute for receipt parsing
- **DynamoDB**: Caching and lightweight persistence with TTL
- **Bedrock Nova**: AI-powered receipt parsing and categorization
- **Terraform**: Infrastructure as Code

## Features

- Parse OCR receipt text into structured JSON
- Automatic GST calculation for Australian receipts
- Hybrid categorization (rules + AI)
- Response caching with DynamoDB TTL
- Comprehensive validation and error handling
- Synthetic data generation for testing
- Evaluation and regression testing framework

## Project Structure

```
├── app/                          # Main application code
│   ├── api/handler.py           # Lambda handler
│   ├── services/receipt_service.py  # Core business logic
│   └── core/                    # Core modules
├── synthetic/                   # Synthetic data generation
├── evaluation/                  # Evaluation and metrics
├── tests/                       # Unit, integration, regression tests
├── infra/terraform/             # Infrastructure as Code
└── requirements.txt             # Python dependencies
```

## Local Setup

1. **Clone and setup Python environment:**
   ```bash
   cd parsing-api
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and settings
   ```

3. **Install Terraform:**
   ```bash
   # Download from https://www.terraform.io/downloads
   terraform --version
   ```

## Deployment

### 1. Deploy Infrastructure

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### 2. Package and Deploy Lambda

```bash
# Package the Lambda function
cd infra/terraform
terraform apply  # This will create the ZIP from ../app

# Or manually:
cd app
zip -r ../infra/terraform/lambda_function.zip . -x "*.pyc" "__pycache__/*"
```

### 3. Update Lambda Environment Variables

After deployment, update the Lambda function with actual values:
- `BEDROCK_MODEL_ID`: Your Nova model ID
- `AWS_REGION`: Your AWS region
- `DYNAMODB_TABLE_NAME`: From Terraform output

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Regression Tests
```bash
# Generate synthetic data
python synthetic/generator.py

# Run evaluation
python evaluation/evaluator.py --predictions synthetic/evaluation_data.jsonl --ground-truth synthetic/evaluation_data.jsonl

# Run regression test
python evaluation/regression_runner.py --test-data synthetic/evaluation_data.jsonl --predictions synthetic/evaluation_data.jsonl
```

## API Usage

### Endpoint
```
POST {api-endpoint}/v1/receipts/parse
```

### Request Format
```json
{
  "receipt_text": "STARBUCKS\nTotal: $5.50\nGST: $0.50",
  "currency": "AUD",
  "source": "app",
  "user_id": "user123",
  "metadata": {
    "device": "iPhone"
  }
}
```

### Response Format
```json
{
  "vendor": "STARBUCKS",
  "receipt_date": "2024-01-15",
  "items": [
    {
      "name": "Coffee",
      "quantity": 1,
      "unit_price": 5.0,
      "total_price": 5.0
    }
  ],
  "subtotal_amount": 5.0,
  "total_amount": 5.5,
  "gst_amount": 0.5,
  "currency": "AUD",
  "category": "Food",
  "categorization_source": "rules",
  "categorization_reason": "Matched keywords: starbucks",
  "matched_keywords": ["starbucks"],
  "confidence_score": 0.95,
  "cache_status": "miss",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "warnings": []
}
```

### Sample cURL Request
```bash
curl -X POST "{api-endpoint}/v1/receipts/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_text": "BP\nFuel: $50.00\nTotal: $50.00",
    "currency": "AUD"
  }'
```

## Configuration

### Required AWS Permissions
- Bedrock: InvokeModel for Nova
- DynamoDB: GetItem, PutItem, Query
- CloudWatch: Create logs

### Environment Variables
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `BEDROCK_MODEL_ID`: Amazon Nova model ID
- `DYNAMODB_TABLE_NAME`: Cache table name
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Development

### Adding New Categories
Update `app/core/categorizer.py` RULES dictionary.

### Modifying GST Logic
Update `app/core/normalizer.py` compute_gst method.

### Custom Evaluation Metrics
Extend `evaluation/metrics.py`.

## Monitoring

- **CloudWatch Logs**: API Gateway and Lambda logs
- **CloudWatch Metrics**: Lambda duration, errors, invocations
- **DynamoDB**: Cache hit rates and TTL expiration

## Troubleshooting

### Common Issues
1. **Bedrock Access Denied**: Check IAM permissions and model access
2. **DynamoDB Throttling**: Monitor read/write capacity
3. **Lambda Timeout**: Increase timeout for complex receipts
4. **GST Calculation Errors**: Verify Australian GST logic

### Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/scango-receipt-intelligence-parser --follow

# View API Gateway logs
aws logs tail /aws/apigateway/scango-receipt-intelligence-api --follow
```

## Security

- API Gateway request validation
- IAM least privilege access
- DynamoDB TTL for data retention
- Input sanitization and validation
- No sensitive data logging

## Contributing

1. Follow the modular structure
2. Add tests for new features
3. Update documentation
4. Run regression tests before PR

## License

[Add your license here]