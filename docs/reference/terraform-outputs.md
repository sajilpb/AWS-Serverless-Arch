# Terraform Outputs Reference

This page documents key outputs defined in `terraform/output.tf`.

> Note: Refer to `terraform/output.tf` for the authoritative definitions.

## Common Outputs

- **`api_base_url`**
  - Description: Base URL of the API Gateway HTTP API fronting the Lambda function.
  - Usage: Configure the frontend `API_BASE` constant in `frontend/index.html`.

- **CloudFront / Domain Outputs** (if defined)
  - Examples: distribution ID, distribution domain, or full CloudFront URL.
  - Usage: Operations team uses these for DNS, monitoring, and invalidations.

## Usage

From the `terraform/` directory:

```bash
terraform output
terraform output api_base_url
```

Use these values in frontend configuration and during operational runbooks.
