import os
import urllib.parse


def lambda_handler(event, context):
    domain_prefix = os.environ.get("COGNITO_DOMAIN_PREFIX")
    client_id = os.environ.get("COGNITO_CLIENT_ID")
    redirect_uri = os.environ.get("COGNITO_REDIRECT_URI")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not domain_prefix or not client_id or not redirect_uri:
        print("Missing config:", {
            "COGNITO_DOMAIN_PREFIX": domain_prefix,
            "COGNITO_CLIENT_ID": client_id,
            "COGNITO_REDIRECT_URI": redirect_uri,
        })
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": "{\"error\": \"Missing configuration for Cognito redirect\"}"
        }

    hosted_domain = f"{domain_prefix}.auth.{region}.amazoncognito.com"

    path = (
        event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or ""
    )

    if str(path).endswith("/logout"):
        params = {
            "client_id": client_id,
            "logout_uri": redirect_uri,
        }
        url = f"https://{hosted_domain}/logout?{urllib.parse.urlencode(params)}"
    else:
        params = {
            "client_id": client_id,
            "response_type": "token",
            "scope": "openid email",
            "redirect_uri": redirect_uri,
            # optional but recommended to mitigate CSRF
            "state": "login"
        }
        url = f"https://{hosted_domain}/oauth2/authorize?{urllib.parse.urlencode(params)}"

    print("Redirecting to:", url)

    return {
        "statusCode": 302,
        "headers": {"Location": url},
        "body": ""
    }
