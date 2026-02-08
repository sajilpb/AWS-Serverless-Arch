# Terraform Layout

All Infrastructure as Code (IaC) lives under the `terraform/` directory.

## Root Files

- `terraform/main.tf`
  - Composes the major modules: CloudFront, S3, ACM, Cognito, Lambda, API Gateway, DynamoDB.
- `terraform/variables.tf`
  - Input variables such as `s3bucketname`, Cognito domain prefix, Lambda zip path, etc.
- `terraform/locals.tf`
  - Local values such as `my_domain` and other derived settings.
- `terraform/output.tf`
  - Key outputs including `api_base_url` and potentially CloudFront distribution/domain.
- `terraform/provider.tf`
  - AWS provider configuration and region.

## Modules

Each subdirectory under `terraform/modules/` encapsulates a specific concern:

- `modules/cloudfront` – CloudFront distribution pointing to the S3 bucket.
- `modules/S3` – S3 bucket for frontend hosting.
- `modules/acmcertificate` – ACM certificate for the CloudFront custom domain.
- `modules/Cognito` – Cognito User Pool, app client, and Hosted UI configuration.
- `modules/lambda` – Lambda function, IAM role/policies, packaging configuration.
- `modules/apigateway` – API Gateway HTTP API, integration with Lambda.
- `modules/Dynamodb` – DynamoDB table storing EC2 instance records.

## State

- `terraform/terraform.tfstate` (and `.backup`) – Local state for development.
- For production, consider migrating to a **remote backend** (e.g., S3 + DynamoDB) for safer collaboration and locking.

## Basic Workflow

From the repo root:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

After apply:

- Use `terraform output` to fetch URLs and IDs needed by the frontend and operations teams.
