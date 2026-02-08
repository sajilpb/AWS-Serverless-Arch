# Architecture Components

This page describes the main infrastructure components and how they relate to each other.

## Terraform Root

- [terraform/main.tf](../infrastructure/terraform-layout.md) wires together modules for:
  - CloudFront + S3 frontend hosting
  - ACM certificate for your domain
  - Cognito User Pool + Hosted UI
  - Lambda function and its packaging
  - API Gateway HTTP API
  - DynamoDB table

## CloudFront + S3

- **S3 Bucket**
  - Name controlled by `var.s3bucketname` in `terraform/variables.tf`.
  - Hosts the `frontend/index.html` file and related assets.
- **CloudFront Distribution**
  - Uses the S3 bucket as an origin.
  - Fronts your custom domain (from `local.my_domain` in `terraform/locals.tf`).
  - Serves `index.html` as the default root object.

## ACM Certificate

- Issued in the region required by CloudFront (typically `us-east-1`).
- Validates and provides an **ACM certificate ARN** used by CloudFront for HTTPS.

## Cognito

- **User Pool** for authentication and user management.
- **App Client** for browser‑based flows.
- **Hosted UI** for login/logout.
- Callback URL configured as `https://${local.my_domain}/index.html`.

## Lambda

- Single Lambda function (e.g., `login-redirect`) defined under `Backend/`.
- Handles:
  - Login redirect logic.
  - EC2 instance creation.
  - Deletion of a user’s EC2 instances.

## API Gateway HTTP API

- Fronts the Lambda function as an HTTP API.
- Terraform output `api_base_url` is used by the frontend.

## DynamoDB

- Stores EC2 instance metadata associated with a specific user.
- Used by Lambda to look up and delete a user’s instances.
