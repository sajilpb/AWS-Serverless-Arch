# AWS Serverless EC2 Control

Welcome to the infrastructure documentation for the **AWS Serverless EC2 Control** project.

This project is a reference implementation that uses:

- **Terraform** for Infrastructure as Code
- **Amazon Cognito Hosted UI** for authentication
- **AWS Lambda** for backend logic
- **Amazon API Gateway HTTP API** for the public API
- **Amazon DynamoDB** for tracking EC2 instances per user
- **Amazon S3 + Amazon CloudFront** for hosting the frontend

## What you can do

The frontend application (hosted on S3 + CloudFront) allows an authenticated user to:

- Create an EC2 instance
- Delete **all** of their EC2 instances (looked up from DynamoDB using their Cognito identity)

## Where to start

- Read the [Architecture Overview](architecture/overview.md) for a high‑level picture.
- See [Terraform Layout](infrastructure/terraform-layout.md) to understand the IaC structure.
- Follow [Deployment](operations/deployment.md) to (re)deploy the stack.
