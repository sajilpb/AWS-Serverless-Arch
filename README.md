# AWS Serverless Arch (Simple)

Minimal setup: static HTML UI + Lambda APIs.

## What This Deploys
- API Gateway (stage `Prod`) with Lambdas:
  - `POST /create-ec2` → `lambda/create_ec2.py`
  - `DELETE /instances/{id}` → `lambda/delete_instance.py`
- DynamoDB `InstancesTable` (stores created instance IDs)
- Cognito User Pool + App Client + Hosted UI

## Frontend
- File: `frontend/index.html`
- Host this on S3 (optionally behind CloudFront for HTTPS and custom domain like `app.sajil.click`).
- Edit the constants near the top of the file:
  - `CLIENT_ID` → Cognito App Client ID
  - `USER_POOL_DOMAIN` → `<domainPrefix>.auth.<region>.amazoncognito.com`
  - `API_BASE` → your API Gateway stage URL, e.g. `https://abcd1234.execute-api.us-east-1.amazonaws.com/Prod`

## Deploy Backend (SAM)
```bash
cd /Users/sajilpb/Documents/project/AWS-Serverless-Arch
sam build
sam deploy --guided
```
When prompted:
- Stack Name: `aws-serverless-arch`
- Region: `us-east-1`
- Parameters:
  - `DomainPrefix`: unique (e.g., `sajilapp-123`)
  - `CallbackUrl`: your static site URL (e.g., `https://app.sajil.click/`)

After deploy, get outputs:
```bash
aws cloudformation describe-stacks --stack-name aws-serverless-arch \
  --query "Stacks[0].Outputs" --output table
```
Use `UserPoolClientId` for `CLIENT_ID` and `ApiUrl` for `API_BASE`.

## Host Static Page (S3 quick test)
```bash
aws s3 mb s3://app.sajil.click --region us-east-1
aws s3 cp frontend/index.html s3://app.sajil.click/index.html
```
Enable Static website hosting in the S3 console and set index document to `index.html`.

### Better: CloudFront + ACM + Route 53
1. Request ACM cert for `app.sajil.click` in `us-east-1` and validate DNS.
2. Create CloudFront distribution with origin = your S3 bucket, attach cert.
3. Add Route 53 alias A record `app.sajil.click` → CloudFront.
4. Set Cognito App Client `Callback URL` to `https://app.sajil.click/`.

## Use the App
1. Open your static site URL.
2. Click **Login** → complete Hosted UI.
3. Click **Create EC2 Instance**; copy the returned `instance_id`.
4. Paste the `Instance ID` and click **Delete Instance** to terminate.

## Notes
- CORS is enabled on the API in the template.
- Lambdas use `boto3` (available in the runtime); no extra packaging needed.
- IAM is broad for learning; tighten permissions for production.
# Simple Cognito + API Gateway + Lambda (Create EC2)

This repo is a minimal example that shows:
- A frontend with a Cognito Hosted UI login flow
- A Lambda (Python) that creates an EC2 instance using `boto3`
- API Gateway to call the Lambda from the frontend (protected by Cognito User Pool)

Files added:
- `frontend/index.html` — simple page with login and "Create EC2" button
- `frontend/callback.html` — captures Cognito tokens after login
- `lambda/create_ec2.py` — Lambda function that creates an EC2 instance
- `template.yaml` — AWS SAM template to deploy Lambda, API, and Cognito resources

Quick setup

1. Install AWS SAM CLI and bootstrap if needed:

```bash
# macOS (Homebrew)
brew tap aws/tap
brew install aws-sam-cli

# Initialize or bootstrap your environment (one-time)
sam --version
aws configure  # set credentials with deploy permissions
aws cloudformation list-stacks --region us-east-1 || true
sam deploy --guided
```

2. Edit `template.yaml` parameters during `sam deploy --guided`:
- `DomainPrefix`: a unique prefix for your Cognito Hosted UI domain
- `CallbackUrl`: set to where you'll host the frontend callback (e.g. `http://localhost:8000/callback.html`)

3. Deploy the stack with SAM (example):

```bash
sam deploy --guided
```

Note: The SAM template creates a Cognito User Pool and an App Client configured for the Hosted UI.

4. After deployment, the outputs will include the API endpoint and the Cognito domain. Update the frontend constants in `frontend/index.html`:
- `COGNITO_DOMAIN` — your Cognito domain (e.g. `https://{DomainPrefix}.auth.{region}.amazoncognito.com`)
- `CLIENT_ID` — Cognito User Pool App client id
- `API_URL` — the API Gateway endpoint (POST `/create-ec2`)

5. Host frontend files locally for testing. From the `frontend` folder run:

```bash
# Python 3
cd frontend
python3 -m http.server 8000
# Open http://localhost:8000/index.html
```

6. Click "Login" to go to the Cognito Hosted UI, sign up or sign in, then return. The callback page stores a token and returns to the index page.

7. Click "Create EC2" to call the API (the `Authorization: Bearer <id_token>` header is included).

Security & Permissions

- The Lambda needs EC2 permissions. The SAM template provides minimal IAM statements for `ec2:RunInstances`, `ec2:DescribeImages`, and `ec2:CreateTags`.
- For production, restrict permissions and AMI usage appropriately.

Caveats

- The simple frontend contains placeholders you must fill with values from the deployed stack.
- Hosted UI domain prefixes must be globally unique.
- Running this will create EC2 resources that may incur costs; remember to terminate instances.

If you want, I can deploy the stack for you (if you provide credentials) or walk through the `sam deploy` step interactively.