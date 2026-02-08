# Deployment Guide

This guide explains how to deploy or update the infrastructure using Terraform.

## Prerequisites

- AWS CLI configured with credentials that can create the required resources.
- Terraform installed (matching the version used when the repo was last applied).
- Appropriate DNS / domain set up for the CloudFront distribution.

## Deploying Infrastructure

From the repo root:

```bash
cd terraform

# One‑time setup
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply
```

Terraform will create or update:

- Cognito User Pool + App Client + Hosted UI
- Lambda function for login/redirect + EC2 control
- API Gateway HTTP API
- DynamoDB table for instance records
- S3 bucket for the frontend
- CloudFront distribution and ACM certificate

## Post‑Apply Steps

1. Retrieve the API base URL:

   ```bash
   cd terraform
   terraform output api_base_url
   ```

2. Update the frontend to use the new URL (see [Frontend](frontend.md)).

3. Upload the updated `index.html` file to the S3 bucket and, if needed, invalidate CloudFront.
