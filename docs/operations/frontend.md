# Frontend Operations

This page describes how to configure and deploy the frontend single‑page app.

## Source Location

- Frontend entry point: `frontend/index.html`
- The HTML file contains JavaScript that calls the backend API.

## Configure API Base URL

After Terraform apply, fetch the API base URL:

```bash
cd terraform
terraform output api_base_url
```

In `frontend/index.html`, locate the line:

```js
const API_BASE = 'https://your-api-id.execute-api.us-east-1.amazonaws.com';
```

Update it to match the actual value from Terraform outputs, for example:

```js
const API_BASE = 'https://abcd1234.execute-api.us-east-1.amazonaws.com';
```

Save the file.

## Upload to S3

The S3 bucket name is controlled by `var.s3bucketname` in `terraform/variables.tf` (default: `froneendtwebsite2026`).

To upload the frontend:

```bash
# From the repo root
aws s3 cp frontend/index.html s3://<YOUR_BUCKET_NAME>/index.html --region us-east-1
```

Replace `<YOUR_BUCKET_NAME>` with the value of `s3bucketname`.

## CloudFront

- CloudFront is configured to use the S3 bucket as an origin.
- The distribution uses the custom domain from `local.my_domain`.

If you update `index.html` and changes do not appear immediately, create an invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id <YOUR_DISTRIBUTION_ID> \
  --paths /index.html
```

## Verifying the Frontend

1. Browse to your CloudFront domain (e.g., `https://your-domain.example.com/`).
2. Click **Login** and complete the Cognito Hosted UI flow.
3. Create and delete EC2 instances to verify end‑to‑end behavior.
