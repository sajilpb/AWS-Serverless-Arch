# Terraform Modules

This page summarizes the Terraform modules under `terraform/modules/`.

## Module List

- **acmcertificate**
  - Creates/validates an ACM certificate used by CloudFront for HTTPS.

- **apigateway**
  - Creates the API Gateway HTTP API and integrates it with the Lambda function.

- **cloudfront**
  - Creates the CloudFront distribution with the S3 bucket as an origin.
  - Configures custom domain + ACM certificate.

- **Cognito**
  - Creates Cognito User Pool and Hosted UI configuration.
  - Configures callback URL to your CloudFront domain.

- **Dynamodb**
  - Creates the DynamoDB table used to track EC2 instances per user.

- **lambda**
  - Packages and deploys the Lambda function (source under `Backend/`).
  - Grants IAM permissions required for API/DynamoDB/EC2 operations.

- **S3**
  - Creates the S3 bucket used to host the static frontend.

## How to Extend

If you add new modules, also add them to the navigation in `mkdocs.yml` and update this page.
