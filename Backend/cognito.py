from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use a secure random key in production
oauth = OAuth(app)

# Read configuration from environment variables provided by Lambda
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("COGNITO_REDIRECT_URI")  # e.g., https://your-domain/index.html
OIDC_SCOPES = os.environ.get("OIDC_SCOPES", "email openid")

if not USER_POOL_ID or not CLIENT_ID or not REDIRECT_URI:
    # Fail fast to surface misconfiguration early
    missing = {
        "COGNITO_USER_POOL_ID": USER_POOL_ID,
        "COGNITO_CLIENT_ID": CLIENT_ID,
        "COGNITO_REDIRECT_URI": REDIRECT_URI,
    }
    raise RuntimeError(f"Missing required Cognito env vars: {missing}")

ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}"
SERVER_METADATA_URL = f"{ISSUER}/.well-known/openid-configuration"

oauth.register(
    name="oidc",
    client_id=CLIENT_ID,
    client_secret=(CLIENT_SECRET or None),
    server_metadata_url=SERVER_METADATA_URL,
    client_kwargs={"scope": OIDC_SCOPES},
)



@app.route('/login')
def login():
    # Alternate option to redirect to /authorize
    # redirect_uri = url_for('authorize', _external=True)
    # return oauth.oidc.authorize_redirect(redirect_uri)
    return oauth.oidc.authorize_redirect(REDIRECT_URI)

@app.route('/authorize')
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token['userinfo']
    session['user'] = user
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/ec2-instances')


if __name__ == '__main__':
    app.run(debug=True)