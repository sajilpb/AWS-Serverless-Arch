from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from ...ports import ComputePort, CreateInstanceSpec


class Ec2ComputeAdapter(ComputePort):
    def __init__(self, *, region: str, ami_id_override: str | None = None) -> None:
        self._region = region
        self._ami_id_override = ami_id_override

    def _client(self):
        return boto3.client("ec2", region_name=self._region)

    def _find_latest_amzn2_ami(self, ec2) -> str | None:
        name_patterns = [
            "amzn2-ami-hvm-*-x86_64-gp3",
            "amzn2-ami-hvm-*-x86_64-gp2",
        ]
        for pat in name_patterns:
            try:
                resp = ec2.describe_images(
                    Owners=["amazon"],
                    Filters=[
                        {"Name": "name", "Values": [pat]},
                        {"Name": "state", "Values": ["available"]},
                    ],
                )
            except Exception:
                continue

            images = resp.get("Images", []) or []
            if images:
                images.sort(key=lambda i: i.get("CreationDate", ""), reverse=True)
                return images[0].get("ImageId")
        return None

    def _resolve_default_network(self, ec2) -> tuple[str, str, str]:
        vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}]).get("Vpcs", [])
        if not vpcs:
            raise RuntimeError(f"No default VPC found in region {self._region}")
        default_vpc_id = vpcs[0]["VpcId"]

        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [default_vpc_id]}]).get(
            "Subnets", []
        )
        if not subnets:
            raise RuntimeError(f"No subnets found in default VPC {default_vpc_id}")
        subnet_id = subnets[0]["SubnetId"]

        sgs = ec2.describe_security_groups(
            Filters=[
                {"Name": "vpc-id", "Values": [default_vpc_id]},
                {"Name": "group-name", "Values": ["default"]},
            ]
        ).get("SecurityGroups", [])
        if not sgs:
            raise RuntimeError(f"No default security group found in VPC {default_vpc_id}")
        sg_id = sgs[0]["GroupId"]

        return default_vpc_id, subnet_id, sg_id

    def create_instance(self, spec: CreateInstanceSpec) -> str:
        ec2 = self._client()

        ami = self._ami_id_override or spec.ami_id
        if not ami:
            ami = self._find_latest_amzn2_ami(ec2)
        if not ami:
            raise RuntimeError("No AMI found")

        _, subnet_id, sg_id = self._resolve_default_network(ec2)

        run_args: dict = {
            "ImageId": ami,
            "InstanceType": spec.instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "SubnetId": subnet_id,
            "SecurityGroupIds": [sg_id],
        }
        if spec.key_name:
            run_args["KeyName"] = spec.key_name

        try:
            resp = ec2.run_instances(**run_args)
        except ClientError as e:
            # Keep the original AWS error detail
            raise e

        instance_id = resp["Instances"][0]["InstanceId"]
        try:
            ec2.create_tags(Resources=[instance_id], Tags=[{"Key": "CreatedBy", "Value": spec.created_by_tag_value}])
        except Exception:
            pass

        return instance_id

    def terminate_instances(self, instance_ids) -> None:
        if not instance_ids:
            return
        self._client().terminate_instances(InstanceIds=list(instance_ids))
