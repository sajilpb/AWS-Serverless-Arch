# Architecture Overview

This project implements a **serverless EC2 control plane** on AWS. Users authenticate via Cognito, then interact with a Lambda‑backed HTTP API to create and delete EC2 instances that are associated with their identity.

## High‑Level Diagram (Logical)

- **Client (Browser)**
  - Loads the single‑page frontend from **CloudFront** (backed by an S3 bucket).
  - Redirects users to Cognito Hosted UI for login and logout.
  - Calls the backend API to create and delete EC2 instances.

- **Identity**
  - **Amazon Cognito User Pool** for user management.
  - **Hosted UI** for login/logout flows.
  - After sign‑in, Cognito redirects back to your CloudFront URL with tokens.

- **Backend**
  - **AWS Lambda (login_redirect)**
    - Handles login/logout redirects.
    - Creates EC2 instances on behalf of the authenticated user.
    - Deletes all EC2 instances associated with the authenticated user.
  - **Amazon API Gateway HTTP API**
    - Public entrypoint for the SPA to invoke Lambda.

- **Data**
  - **Amazon DynamoDB** table (e.g., `InstanceManagementTable`)
    - Stores records of EC2 instances per Cognito user.

- **Frontend Delivery**
  - **Amazon S3** bucket for static frontend assets (e.g., `index.html`).
  - **Amazon CloudFront** distribution in front of the S3 bucket.

## Trust Boundaries

- Public internet → CloudFront → S3 (static assets)
- Authenticated browser → API Gateway → Lambda → DynamoDB + EC2
- Authentication is handled by Cognito; Lambda receives identity via JWT / headers propagated by the frontend.

## Key Design Goals

- **Serverless**: No long‑running servers to manage; only pay per request.
- **Least persistent state**: Only DynamoDB stores per‑user instance mappings.
- **Simple onboarding**: Terraform deploys all shared infrastructure in one go.
