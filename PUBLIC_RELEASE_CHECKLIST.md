# Public Release Checklist

Use this checklist before changing the repository visibility from private to public.

1. **Secrets rotated**  
   - [ ] Any AWS credentials that may have been committed historically have been revoked or rotated.  
   - [ ] Amazon Bedrock keys/permissions validated.

2. **.gitignore reviewed**  
   - [ ] Confirms `.env`, `.env.*`, `.venv/`, `terraform.tfvars`, `*.tfstate`, `*.tfplan`, build artifacts, and local datasets are ignored.

3. **Configuration placeholders**  
   - [ ] `.env.example` updated with placeholders only.  
   - [ ] `infra/terraform/terraform.tfvars.example` uses safe placeholder values.

4. **Documentation**  
   - [ ] README updated with architecture overview, sample request/response, deployment steps, security notes, and portfolio summary.  
   - [ ] OCR responsibility (consumer app) and Bedrock access requirements noted.

5. **Testing status**  
   - [ ] pytest suite run and passing.  
   - [ ] `scripts/run_custom_predictions.py` + `evaluation/evaluator.py` executed with acceptable scores.

6. **Repo hygiene**  
   - [ ] Terraform state files, tfplans, dist ZIPs, and synthetic datasets removed or excluded.  
   - [ ] No machine-specific or noisy files remain.

7. **Security tooling**  
   - [ ] GitHub secret scanning and push protection enabled.  
   - [ ] Any previously exposed secrets documented for rotation.

8. **Final review**  
   - [ ] Manual scan for credentials or endpoints that should remain private.  
   - [ ] PUBLIC_RELEASE_CHECKLIST.md reviewed and committed.
