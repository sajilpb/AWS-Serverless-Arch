# STRIDE Threat Model

This document is a diagram-first STRIDE threat model for the AWS Serverless EC2
Control application. It is intended to be both a learning artifact and a
production-audit checklist for future hardening work.

## Purpose And Scope

The application lets authenticated users request EC2 instance creation,
deletion, and request-status checks through a serverless web interface.

In scope:

- CloudFront and S3 hosted frontend.
- Cognito Hosted UI authentication flow.
- API Gateway HTTP API routes for login, logout, EC2 requests, deletion, and
  request status.
- Lambda `production` alias that handles API Gateway traffic.
- DynamoDB request and instance tracking.
- EventBridge worker flow for asynchronous EC2 operations.
- CodePipeline, CodeBuild, CloudWatch alarms, and native Lambda deployment.

Out of scope for this first pass:

- Human operational processes outside AWS.
- Local developer workstation security.
- Detailed penetration testing.
- Formal compliance mapping.

## Security Objectives

- Only authenticated users can create, delete, or inspect their own EC2
  resources.
- User identity cannot be spoofed by modifying client-side tokens or requests.
- EC2 actions are constrained to approved instance types, regions, AMIs, and
  permissions.
- Sensitive data and tokens are not exposed unnecessarily.
- All security-relevant actions can be audited by user, request, and resource.
- Abuse or accidents cannot create unbounded EC2 cost or service disruption.
- Deployment rollback monitoring remains an operational safety control.

## Data Flow Diagram

```text
                         Trust Boundary: Public Internet

  User Browser
      |
      | 1. Load static app
      v
  CloudFront -----> S3 frontend bucket
      |
      | 2. Redirect for login/logout
      v
  Cognito Hosted UI
      |
      | 3. Access token returned to browser
      v
  User Browser
      |
      | 4. API calls with bearer token
      v
  API Gateway HTTP API
      |
      | 5. Proxy integration to alias
      v
  Lambda login_redirect:production
      |
      | 6. Store/read request status
      v
  DynamoDB InstanceManagementTable
      ^
      |
      | 8. Worker updates request and instance state
      |
  Worker Lambda <----- EventBridge events <----- Lambda login_redirect:production
      |
      | 9. Create or terminate EC2 instances
      v
  EC2


                         Trust Boundary: Deployment Plane

  GitHub repo
      |
      v
  CodePipeline source -> CodeBuild package -> Lambda deploy action
      |
      v
  Lambda version + production alias
      |
      v
  CloudWatch deployment alarms
```

## Actors And Assets

| Type | Item | Notes |
| --- | --- | --- |
| Actor | Anonymous internet user | Can reach CloudFront, Cognito, and public API endpoints. |
| Actor | Authenticated user | Can request EC2 operations for their own identity. |
| Actor | AWS service principals | API Gateway, Lambda, EventBridge, CodePipeline, and CodeBuild assume roles. |
| Actor | Maintainer | Pushes code and applies Terraform. |
| Asset | Cognito tokens | Used by the frontend to call API Gateway. |
| Asset | User identity | Cognito `sub` and email bind requests to a user. |
| Asset | DynamoDB records | Track request status and user-owned EC2 instances. |
| Asset | EC2 instances | Cost-bearing resources created and terminated by the app. |
| Asset | Lambda code and aliases | Backend control plane and deployment target. |
| Asset | IAM roles and policies | Define service authority and blast radius. |
| Asset | Pipeline artifacts | Code package used for Lambda deployment. |
| Asset | CloudWatch logs and alarms | Audit, monitoring, and rollback signals. |

## STRIDE Analysis

| Category | Threat | Current Exposure | Recommended Mitigation |
| --- | --- | --- | --- |
| Spoofing | Client sends a forged bearer token or unsigned JWT-like value. | Lambda has a fallback path that decodes bearer token payload without verifying the signature if API Gateway authorizer claims are absent. | Add an API Gateway JWT authorizer backed by Cognito and trust only verified authorizer claims in Lambda. Remove unsigned token parsing fallback. |
| Spoofing | API Gateway invokes the wrong Lambda identity path. | API Gateway now targets the Lambda alias, but all API Gateway permissions should be qualified to the `production` alias. | Add `qualifier = aws_lambda_alias.production.name` to every API Gateway Lambda permission. |
| Spoofing | Unauthorized AWS service or principal invokes Lambda. | Lambda permissions are route scoped, but should stay explicit and alias scoped. | Keep `source_arn` route restrictions and alias qualifiers. Avoid broad Lambda invoke permissions. |
| Tampering | User modifies request body fields such as `instance_type` or `key_name`. | Backend accepts client-supplied values with limited visible validation. | Validate request inputs server-side using allowlists for instance types, key handling, AMI selection, and region. |
| Tampering | Static frontend content is modified or replaced. | S3/CloudFront host the frontend; public access controls and deployment process need to remain tight. | Keep S3 public access blocked, use CloudFront origin access control, restrict direct bucket access, and audit frontend upload/deploy permissions. |
| Tampering | Pipeline artifact or source branch is modified. | CodePipeline deploys from GitHub and CodeBuild artifacts. | Protect the deployment branch, require pull request review, and restrict CodeStar connection and CodeBuild permissions. |
| Repudiation | User denies creating or deleting EC2 resources. | DynamoDB request tracking exists, but security audit logging is not yet complete. | Log structured audit events with `user_id`, `email`, `request_id`, `action`, `status`, target resource, and API Gateway request ID. |
| Repudiation | Operator cannot prove which code version caused a deployment issue. | CodePipeline and Lambda alias deployment exist, with CloudWatch alarms. | Record source commit, build ID, Lambda version, and alias movement in deployment logs or tags. |
| Information Disclosure | Access token stored in `localStorage` can be stolen by injected script. | Frontend stores `access_token` in `localStorage`. | Prefer authorization code with PKCE and short-lived tokens. Reduce XSS risk with strict CSP and no inline script where practical. |
| Information Disclosure | Backend returns raw exception messages to clients. | Lambda catches generic exceptions and returns `{"error": str(e)}`. | Return generic 5xx responses to clients and log detailed errors server-side. |
| Information Disclosure | Overly broad logs expose sensitive data. | API Gateway access logs and Lambda errors may include request details. | Avoid logging tokens or secrets. Review log formats and redact sensitive headers and payload fields. |
| Denial of Service | User or attacker creates many EC2 requests and drives cost. | Create/delete endpoints can be repeatedly called. | Add API Gateway throttling, per-user quotas, service quotas, and request state checks to prevent duplicate or excessive work. |
| Denial of Service | Lambda is throttled or held at reserved concurrency zero during tests. | Reserved concurrency can block production traffic if left at `0`. | Remove test throttling after validation. Use controlled load tests and alarm-state checks in dev only. |
| Denial of Service | Worker receives too many EventBridge events. | Worker processes async EC2 operations and has broad EC2 authority. | Add concurrency limits, dead-letter queues, retry policies, and alarms for worker failures and backlog. |
| Elevation of Privilege | Lambda or worker role can affect more AWS resources than required. | IAM policies include broad `resources = ["*"]` for EC2, DynamoDB, logs, and other actions. | Scope DynamoDB to the table ARN. Scope EventBridge to intended bus/rules. Constrain EC2 actions with tags, allowed instance types, regions, and resource conditions where AWS supports them. |
| Elevation of Privilege | API caller acts as another user. | Authorization depends on identity extraction and DynamoDB access patterns. | Use verified Cognito `sub` from API Gateway authorizer and require all request/status/delete operations to key by that `sub`. |
| Elevation of Privilege | Pipeline role can update unintended Lambda resources. | Pipeline role has Lambda deployment permissions for the selected function and alias resources. | Keep Lambda permissions scoped to the target function and alias. Avoid wildcard deployment permissions outside learning environments. |

## Flow-Specific Notes

### Login And Logout

- The browser starts login by calling `GET /login`, and Lambda redirects to
  Cognito Hosted UI.
- Cognito returns a token to the frontend callback URL.
- Threat focus: token theft, token spoofing, open redirect mistakes, and weak
  OAuth flow choices.
- Recommended next step: move from implicit flow to authorization code with
  PKCE, then configure API Gateway JWT authorizer.

### Create EC2 Request

- Browser calls `POST /create-ec2` with a bearer token.
- Lambda extracts the user identity, creates a request record, and emits an
  EventBridge event.
- Worker creates the EC2 instance and updates DynamoDB.
- Threat focus: spoofed identity, unbounded cost, input tampering, broad EC2
  permissions, and missing audit trail.
- Recommended next step: validate instance inputs and add per-user quotas before
  creating requests.

### Delete EC2 Request

- Browser calls `DELETE /instances` or `DELETE /instances/{id}`.
- Lambda creates an async termination request.
- Worker terminates instances associated with the user.
- Threat focus: deleting another user's resources, replayed requests, and
  overbroad EC2 termination permissions.
- Recommended next step: ensure all delete operations are constrained by
  verified Cognito `sub` and DynamoDB ownership records.

### Request Status Polling

- Browser calls `GET /requests/{id}`.
- Lambda reads request state for the authenticated user.
- Threat focus: ID guessing and cross-user status disclosure.
- Recommended next step: require verified user identity and always query by
  `user_id` plus `request_id`.

### CodePipeline Lambda Deployment

- CodePipeline pulls from GitHub, CodeBuild produces the Lambda artifact, and
  the native Lambda deploy action updates the `production` alias.
- CloudWatch alarms are used for deployment rollback monitoring.
- Threat focus: supply-chain tampering, overly broad deployment role, and weak
  rollback signal coverage.
- Recommended next step: keep branch protection, scoped IAM, and alarm-based
  rollback, but treat deployment alarms as operational controls rather than
  preventive security controls.

## Prioritized Mitigation Backlog

| Priority | Mitigation | Category |
| --- | --- | --- |
| P0 | Add API Gateway JWT authorizer for Cognito and remove unsigned token parsing fallback. | Spoofing, Elevation of Privilege |
| P0 | Return generic 5xx responses and log detailed errors server-side only. | Information Disclosure |
| P0 | Add server-side allowlists for EC2 instance type, region, AMI, and key handling. | Tampering, Denial of Service |
| P1 | Restrict CORS to the CloudFront/custom domain instead of `*`. | Information Disclosure, Tampering |
| P1 | Add structured audit logging for all create/delete/status operations. | Repudiation |
| P1 | Add API Gateway throttling and per-user quotas for EC2 operations. | Denial of Service |
| P1 | Scope IAM policies to specific DynamoDB, EventBridge, Lambda, and supported EC2 constraints. | Elevation of Privilege |
| P1 | Add alias-qualified API Gateway Lambda permissions for every route. | Spoofing |
| P2 | Move frontend auth from implicit flow/localStorage toward authorization code with PKCE. | Information Disclosure, Spoofing |
| P2 | Add worker dead-letter queue, retry alarms, and backlog/failure dashboards. | Denial of Service, Repudiation |
| P2 | Tag deployments with commit SHA, pipeline execution ID, and Lambda version. | Repudiation |

## Open Questions

- Should users be allowed to choose EC2 instance type and key name, or should
  those be fully server-controlled?
- What is the expected maximum number of active EC2 instances per user?
- Should request history be retained indefinitely, or expire after a fixed
  period?
- Is this environment only for learning/dev, or should the Terraform defaults be
  production-safe by default?

## Review Checklist

- Every public API route has an authentication and authorization story.
- Every EC2 action is tied to a verified Cognito `sub`.
- Every cost-bearing operation has a quota or rate limit.
- Every security-relevant action has an audit log entry.
- Every broad IAM permission has a tracked follow-up to scope it down.
- Deployment monitoring is present, but not treated as a substitute for
  preventive security controls.
