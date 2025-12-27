# AWS Serverless EC2 Control

Serverless reference implementation using:
- Terraform for infrastructure
- Lambda + API Gateway HTTP API for backend
- Cognito Hosted UI for authentication
- DynamoDB for tracking EC2 instances per user
- S3 + CloudFront for hosting the frontend

The frontend lets an authenticated user:
- Create an EC2 instance
- Delete all of their own instances (looked up from DynamoDB)

---

## 1. Deploy Infrastructure with Terraform

All IaC lives under the `terraform` directory.

From the repo root:

```bash
cd terraform

# First-time setup
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply
```

Terraform creates (among other things):
- Cognito User Pool + App Client + Hosted UI
- Lambda `login-redirect` (handles login/logout + EC2 create/delete)
- HTTP API Gateway
- DynamoDB table `InstanceManagementTable`
- S3 bucket for the frontend (name from `var.s3bucketname`)
- CloudFront distribution in front of the S3 bucket

After apply, you can retrieve the API base URL with:

```bash
cd terraform
terraform output api_base_url
```

Copy this value; you will use it in the frontend.

---

## 2. Configure the Frontend (API URL)

Frontend entry point is [frontend/index.html](frontend/index.html).

Near the top of the script block you will see:

```js
const API_BASE = 'https://your-api-id.execute-api.us-east-1.amazonaws.com';
```

Update this line so that `API_BASE` matches the value from `terraform output api_base_url`, for example:

```js
const API_BASE = 'https://abcd1234.execute-api.us-east-1.amazonaws.com';
```

Save the file after editing.

---

## 3. Upload `index.html` to the S3 Bucket

Terraform creates the frontend S3 bucket using the `s3bucketname` variable defined in [terraform/variables.tf](terraform/variables.tf). The default in this repo is `froneendtwebsite2026`.

To upload the updated `index.html`:

```bash
# From the repo root
aws s3 cp frontend/index.html s3://froneendtwebsite2026/index.html --region us-east-1
```

If you changed `s3bucketname`, replace `froneendtwebsite2026` with your actual bucket name.

CloudFront is already configured to serve `index.html` as the default root object for your domain (from `local.my_domain` in [terraform/locals.tf](terraform/locals.tf)). After upload, invalidate CloudFront if you still see an old version:

```bash
aws cloudfront create-invalidation \
  --distribution-id <YOUR_DISTRIBUTION_ID> \
  --paths /index.html
```

---

## 4. Using the App

1. Browse to your CloudFront domain (for example, `https://sajil.click/`).
2. Click **Login** and complete the Cognito Hosted UI flow.
3. After redirect back, click **Create EC2 Instance**.
4. When you are done, click **Delete My Instances** to terminate all EC2 instances associated with your Cognito user and remove their records from DynamoDB.

---

## 5. Notes & Safety

- EC2 instances incur cost while running; ensure you delete them when finished.
- Terraform state files can contain identifiers and configuration; prefer a remote backend (S3 + DynamoDB) for production.
- IAM policies are intentionally broad for learning; tighten them before using in a real environment.