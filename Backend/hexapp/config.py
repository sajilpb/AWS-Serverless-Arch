from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    cognito_domain_prefix: str
    cognito_client_id: str
    cognito_redirect_uri: str
    aws_region: str

    oidc_scopes: str

    ddb_table_name: str
    default_instance_type: str
    ami_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        return cls(
            cognito_domain_prefix=os.environ.get("COGNITO_DOMAIN_PREFIX", ""),
            cognito_client_id=os.environ.get("COGNITO_CLIENT_ID", ""),
            cognito_redirect_uri=os.environ.get("COGNITO_REDIRECT_URI", ""),
            aws_region=region,
            oidc_scopes=os.environ.get("OIDC_SCOPES") or "openid email",
            ddb_table_name=os.environ.get("DDB_TABLE_NAME") or "InstanceManagementTable",
            default_instance_type=os.environ.get("INSTANCE_TYPE") or "t2.micro",
            ami_id=os.environ.get("AMI_ID") or None,
        )

    def validate_auth_config(self) -> None:
        missing = []
        if not self.cognito_domain_prefix:
            missing.append("COGNITO_DOMAIN_PREFIX")
        if not self.cognito_client_id:
            missing.append("COGNITO_CLIENT_ID")
        if not self.cognito_redirect_uri:
            missing.append("COGNITO_REDIRECT_URI")
        if missing:
            raise ValueError("Missing configuration for Cognito redirect: " + ", ".join(missing))

    @property
    def cognito_hosted_domain(self) -> str:
        # Example: <prefix>.auth.<region>.amazoncognito.com
        return f"{self.cognito_domain_prefix}.auth.{self.aws_region}.amazoncognito.com"
