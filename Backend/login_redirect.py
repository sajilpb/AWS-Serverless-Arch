import os
import urllib.parse
import json
import base64
import boto3
import traceback
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


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

    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "GET"
    )
    print({"path": path, "method": method})

    # Try to extract Cognito user information
    # 1) Prefer JWT authorizer claims (if an authorizer is configured on the HTTP API)
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    jwt_ctx = authorizer.get("jwt") or {}
    claims = jwt_ctx.get("claims", {})
    cognito_sub = claims.get("sub")
    cognito_email = claims.get("email") or claims.get("cognito:username")

    # 2) If no claims (no authorizer attached), fall back to decoding the Authorization header JWT
    if not cognito_sub:
        headers = event.get("headers", {}) or {}
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header and isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            print("Attempting to decode JWT from Authorization header")
            try:
                parts = token.split(".")
                if len(parts) == 3:
                    payload_b64 = parts[1]
                    # Fix padding for base64url
                    padding = "=" * (-len(payload_b64) % 4)
                    payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
                    payload = json.loads(payload_bytes.decode("utf-8"))
                    cognito_sub = payload.get("sub")
                    cognito_email = payload.get("email") or payload.get("cognito:username")
                    print("Decoded JWT payload claims:", {"sub": cognito_sub, "email": cognito_email})
                else:
                    print("JWT format unexpected, parts:", len(parts))
            except Exception as jwt_err:
                print("JWT decode error:", repr(jwt_err))

    if cognito_sub or cognito_email:
        print("Cognito user claims (final):", {"sub": cognito_sub, "email": cognito_email})

    if str(path).endswith("/logout") and method == "GET":
        params = {
            "client_id": client_id,
            "logout_uri": redirect_uri,
        }
        url = f"https://{hosted_domain}/logout?{urllib.parse.urlencode(params)}"
    elif str(path).endswith("/login") and method == "GET":
        params = {
            "client_id": client_id,
            "response_type": "token",
            "scope": "openid email",
            "redirect_uri": redirect_uri,
            # optional but recommended to mitigate CSRF
            "state": "login"
        }
        url = f"https://{hosted_domain}/oauth2/authorize?{urllib.parse.urlencode(params)}"
    elif str(path).endswith("/create-ec2") and method == "POST":
        print("/create-ec2 handler entered")
        print("Environment snapshot for EC2:", {
            "AWS_REGION": region,
            "AMI_ID": os.environ.get("AMI_ID","ami-068c0051b15cdb816"),
            "INSTANCE_TYPE": os.environ.get("INSTANCE_TYPE", "t2.micro"),
        })
        try:
            # Log runtime identity to verify which IAM role is in effect
            sts = boto3.client("sts", region_name=region)
            try:
                ident = sts.get_caller_identity()
                print("STS identity:", ident)
            except Exception as id_err:
                print("STS identity error:", repr(id_err))

            ec2 = boto3.client("ec2", region_name=region)
            ami_env = os.environ.get("AMI_ID")
            default_instance_type = os.environ.get("INSTANCE_TYPE", "t2.micro")

            print("Raw event keys:", list(event.keys()))
            body = event.get("body")
            print("Raw body type and preview:", type(body).__name__, str(body)[:200])
            if isinstance(body, str) and body:
                try:
                    body = json.loads(body)
                except Exception as parse_err:
                    print("Body JSON parse error:", repr(parse_err))
                    body = {}
            elif body is None:
                body = {}

            print("Parsed body:", body)
            instance_type = body.get("instance_type") or default_instance_type
            print("Create EC2 request:", {"instance_type": instance_type, "region": region})

            def find_latest_amzn2_ami():
                print("Finding latest Amazon Linux 2 AMI...")
                name_patterns = [
                    "amzn2-ami-hvm-*-x86_64-gp3",
                    "amzn2-ami-hvm-*-x86_64-gp2",
                ]
                for pat in name_patterns:
                    print("Describing images with pattern:", pat)
                    try:
                        resp = ec2.describe_images(
                            Owners=["amazon"],
                            Filters=[
                                {"Name": "name", "Values": [pat]},
                                {"Name": "state", "Values": ["available"]},
                            ],
                        )
                    except Exception as desc_err:
                        print("describe_images error for pattern", pat, ":", repr(desc_err))
                        continue

                    images = resp.get("Images", [])
                    print(f"describe_images returned {len(images)} images for pattern {pat}")
                    if images:
                        images.sort(key=lambda i: i.get("CreationDate", ""), reverse=True)
                        chosen = images[0].get("ImageId")
                        print("Chosen AMI from describe_images:", chosen)
                        return chosen
                print("No images matched any pattern")
                return None

            print("AMI from environment:", ami_env)
            ami = ami_env or find_latest_amzn2_ami()
            print("Final AMI selected:", ami)
            if not ami:
                print("AMI lookup failed - returning 500")
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "No AMI found"}),
                }

            # Find default VPC, one subnet in it, and default security group
            try:
                vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}]).get("Vpcs", [])
                if not vpcs:
                    raise RuntimeError("No default VPC found in region " + region)
                default_vpc_id = vpcs[0]["VpcId"]
                print("Default VPC:", default_vpc_id)

                subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [default_vpc_id]}]).get("Subnets", [])
                if not subnets:
                    raise RuntimeError("No subnets found in default VPC " + default_vpc_id)
                subnet_id = subnets[0]["SubnetId"]
                print("Using subnet:", subnet_id)

                sgs = ec2.describe_security_groups(Filters=[{"Name": "vpc-id", "Values": [default_vpc_id]}, {"Name": "group-name", "Values": ["default"]}]).get("SecurityGroups", [])
                if not sgs:
                    raise RuntimeError("No default security group found in VPC " + default_vpc_id)
                sg_id = sgs[0]["GroupId"]
                print("Using security group:", sg_id)

                # Log consolidated network selection for easier debugging
                print("EC2 network selection:", {
                    "vpc_id": default_vpc_id,
                    "subnet_id": subnet_id,
                    "security_group_id": sg_id,
                })
            except Exception as net_err:
                print("Network lookup (VPC/Subnet/SG) error:", repr(net_err))
                raise

            run_args = {
                "ImageId": ami,
                "InstanceType": instance_type,
                "MinCount": 1,
                "MaxCount": 1,
                "SubnetId": subnet_id,
                "SecurityGroupIds": [sg_id],
            }

            # Optional key pair support: if client passes key_name/KeyName, use it; otherwise no key pair
            key_name = body.get("key_name") or body.get("KeyName") if isinstance(body, dict) else None
            if key_name:
                run_args["KeyName"] = key_name
                print("Using provided key pair:", key_name)
            else:
                print("No key pair specified, launching without SSH key (SSM-only or console-less access)")

            print("Calling run_instances with args:", run_args)
            try:
                resp = ec2.run_instances(**run_args)
            except Exception as run_err:
                print("run_instances error:", repr(run_err))
                if isinstance(run_err, ClientError):
                    try:
                        print("run_instances ClientError response:", json.dumps(run_err.response, default=str))
                    except Exception as resp_err:
                        print("Error serializing ClientError response:", repr(resp_err))
                raise

            print("run_instances raw response keys:", list(resp.keys()))
            instance_id = resp["Instances"][0]["InstanceId"]
            print("EC2 instance created:", instance_id)
            try:
                ec2.create_tags(Resources=[instance_id], Tags=[{"Key": "CreatedBy", "Value": "UnifiedLambda"}])
            except Exception as tag_err:
                print("Tagging failed:", repr(tag_err))

            # Write instance details to DynamoDB if we have a Cognito user id
            table_name = os.environ.get("DDB_TABLE_NAME") or "InstanceManagementTable"
            print("DynamoDB config:", {"table_name": table_name, "cognito_sub_present": bool(cognito_sub)})
            if cognito_sub and table_name:
                try:
                    ddb = boto3.resource("dynamodb", region_name=region)
                    table = ddb.Table(table_name)
                    item = {
                        "user_id": cognito_sub,
                        "instance_id": instance_id,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "region": region,
                        "instance_type": instance_type,
                        "state": "pending",
                    }
                    if cognito_email:
                        item["email"] = cognito_email
                    print("Putting item to DynamoDB:", {"table": table_name, "item": item})
                    table.put_item(Item=item)
                    print("DynamoDB put_item succeeded")
                except Exception as ddb_err:
                    print("DynamoDB put_item error:", repr(ddb_err))
            else:
                print("Skipping DynamoDB write - missing user id or table name")

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"instance_id": instance_id}),
            }
        except Exception as e:
            print("Create EC2 error (top-level handler):", repr(e))
            error_payload = {"message": str(e)}
            if isinstance(e, ClientError):
                try:
                    err_resp = e.response or {}
                except Exception as resp_err:
                    print("Error reading ClientError.response:", repr(resp_err))
                    err_resp = {}
                try:
                    print("ClientError full response:", json.dumps(err_resp, default=str))
                except Exception as ser_err:
                    print("Error serializing ClientError full response:", repr(ser_err))
                error_payload.update({
                    "code": err_resp.get("Error", {}).get("Code"),
                    "detail": err_resp.get("Error", {}).get("Message"),
                })
            traceback.print_exc()
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": error_payload}),
            }
    elif (str(path).startswith("/instances")) and method == "DELETE":
        print("/instances DELETE handler entered", {"path": path})
        ec2 = boto3.client("ec2", region_name=region)
        table_name = os.environ.get("DDB_TABLE_NAME") or "InstanceManagementTable"

        raw_path = str(path)
        # If path is exactly /instances (optionally with trailing slash), treat as bulk delete
        if raw_path.rstrip("/") == "/instances":
            inst_id = ""
        else:
            # Expect /instances/{id} and extract the part after '/instances/'
            parts = raw_path.split("/instances/", 1)
            inst_id = parts[1].strip() if len(parts) == 2 else ""
        print("Resolved inst_id from path:", inst_id or "<none>")

        # If no specific instance id is supplied, delete all instances for this Cognito user
        if not inst_id:
            print("No instance id in path; attempting per-user bulk delete")
            if not cognito_sub:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Missing instance id and user id; cannot resolve which instances to delete"}),
                }
            if not table_name:
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "DynamoDB table name not configured"}),
                }

            try:
                ddb = boto3.resource("dynamodb", region_name=region)
                table = ddb.Table(table_name)
                print("Querying DynamoDB for user instances", {"table": table_name, "user_id": cognito_sub})
                query_resp = table.query(KeyConditionExpression=Key("user_id").eq(cognito_sub))
                items = query_resp.get("Items", [])
                print("DynamoDB returned items:", items)
                instance_ids = [it["instance_id"] for it in items if "instance_id" in it]
                if not instance_ids:
                    return {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"message": "No instances found for user"}),
                    }

                print("Terminating instances:", instance_ids)
                ec2.terminate_instances(InstanceIds=instance_ids)

                # Remove records from DynamoDB
                for iid in instance_ids:
                    try:
                        table.delete_item(Key={"user_id": cognito_sub, "instance_id": iid})
                    except Exception as del_err:
                        print("DynamoDB delete_item error for instance", iid, ":", repr(del_err))

                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"terminated": instance_ids}),
                }
            except Exception as e:
                print("Bulk delete error:", repr(e))
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)}),
                }

        # Fallback: delete a specific instance id from the path
        try:
            print("Deleting single instance from path:", inst_id)
            ec2.terminate_instances(InstanceIds=[inst_id])
            if table_name and cognito_sub:
                try:
                    ddb = boto3.resource("dynamodb", region_name=region)
                    table = ddb.Table(table_name)
                    table.delete_item(Key={"user_id": cognito_sub, "instance_id": inst_id})
                except Exception as del_err:
                    print("DynamoDB delete_item error for single instance:", repr(del_err))
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)}),
            }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"terminated": inst_id}),
        }
    else:
        # default: redirect to login
        params = {
            "client_id": client_id,
            "response_type": "token",
            "scope": "openid email",
            "redirect_uri": redirect_uri,
            "state": "login",
        }
        url = f"https://{hosted_domain}/oauth2/authorize?{urllib.parse.urlencode(params)}"

    print("Redirecting to:", url)

    return {
        "statusCode": 302,
        "headers": {"Location": url},
        "body": ""
    }
