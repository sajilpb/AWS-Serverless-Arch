import os
import urllib.parse
import json
import boto3
import traceback
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

    # Try to extract Cognito user information from JWT authorizer (HTTP API)
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    jwt = authorizer.get("jwt") or {}
    claims = jwt.get("claims", {})
    cognito_sub = claims.get("sub")
    cognito_email = claims.get("email") or claims.get("cognito:username")
    if cognito_sub or cognito_email:
        print("Cognito user claims:", {"sub": cognito_sub, "email": cognito_email})

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
    elif (str(path).startswith("/instances/") or str(path).startswith("/instances")) and method == "DELETE":
        ec2 = boto3.client("ec2", region_name=region)
        # extract the instance id from the raw path
        inst_id = str(path).split("/instances/")[-1]
        inst_id = inst_id.strip()
        if not inst_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Missing instance id"}),
            }
        try:
            ec2.terminate_instances(InstanceIds=[inst_id])
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
