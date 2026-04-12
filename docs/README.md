# ScanGo Receipt Intelligence – Technical Overview

## System Diagram (Narrative)
1. Mobile/partner apps send OCR text to the API Gateway endpoint (`/v1/receipts/parse`).
2. API Gateway invokes the `receipt-handler` Lambda inside `app/api/handler.py`.
3. `ReceiptService` orchestrates: validate payload, hit DynamoDB cache, call Amazon Bedrock Nova through `BedrockClient`, normalize totals/GST, persist cache entry, and emit metrics/logs.
4. Responses are serialized JSON returned to clients while CloudWatch captures logs/metrics for observability.

## Key Components
- **Application (`app/`)** – Lambda handler, Bedrock client, categorizer, GST normalization, DTO schemas.
- **Infrastructure (`infra/` + Terraform)** – API Gateway, Lambda, DynamoDB, IAM roles, logging/alerts. Everything is codified for reproducibility.
- **Synthetic + Evaluation** – Data generators and regression harness to validate parsing quality release-over-release.
- **Tests (`tests/`)** – Unit/integration suites executed via `pytest` and `run_regression_tests.py`.

## Local Development Workflow
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # populate with non-production credentials
pytest
```
Use the VS Code Python interpreter selector to point at `.venv/bin/python` so linters resolve dependencies.

## Deployment Notes
- `infra/terraform` owns provisioning; run `terraform init/plan/apply` with remote state backends for teams.
- Lambda packaging is automated inside Terraform, but `app/` can be zipped manually if needed.
- Keep Bedrock model IDs, API keys, and Terraform state outside git.

## Security & Secrets
- `.env`, `.env.*`, `secrets.json`, AWS credentials, and `.tfstate` files are ignored via `.gitignore`.
- Review `git status` before every commit; the repo must never include credentials, Bedrock model secrets, or API keys.

## Suggested Talking Points (Resume/Interview)
- Serverless architecture tying together API Gateway, Lambda, DynamoDB, and Bedrock Nova.
- Hybrid rule + LLM parsing, plus synthetic/evaluation tooling to measure accuracy.
- Infrastructure-as-Code discipline with Terraform and clear separation of app vs. infra vs. evaluation assets.
