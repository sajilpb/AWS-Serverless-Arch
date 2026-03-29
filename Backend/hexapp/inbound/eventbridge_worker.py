from __future__ import annotations

from typing import Any


def lambda_handler(event: dict[str, Any], _context: Any) -> None:
    """EventBridge worker for asynchronous EC2 instance provisioning.

    Expects events with:
      - source: app.ec2-control-plane
      - detail-type: InstanceCreateRequested
      - detail: { requestId, userId, email?, instanceType, keyName? }
    """

    detail_type = event.get("detail-type") or event.get("detailType")
    detail = event.get("detail") or {}
    request_id = str(detail.get("requestId") or "").strip()
    user_id = str(detail.get("userId") or "").strip()

    if not (request_id and user_id):
        raise ValueError("Missing required detail fields")

    # Lazy imports to keep module importable without boto3 installed locally.
    from ..application import (
        CreateInstanceForUser,
        ProcessInstanceCreateRequested,
        ProcessInstancesTerminateRequested,
        TerminateInstancesForUser,
        TerminateSingleInstance,
    )
    from ..adapters.aws.clock import UtcClock
    from ..adapters.aws.dynamodb_repo import DynamoDbInstanceRepository
    from ..adapters.aws.dynamodb_requests import DynamoDbRequestRepository
    from ..adapters.aws.ec2_compute import Ec2ComputeAdapter
    from ..config import Settings

    settings = Settings.from_env()

    compute = Ec2ComputeAdapter(region=settings.aws_region, ami_id_override=settings.ami_id)
    instance_repo = DynamoDbInstanceRepository(region=settings.aws_region, table_name=settings.ddb_table_name)
    request_repo = DynamoDbRequestRepository(region=settings.aws_region, table_name=settings.ddb_table_name)
    clock = UtcClock()

    if detail_type == "InstanceCreateRequested":
        instance_type = str(detail.get("instanceType") or "").strip()
        key_name = detail.get("keyName")
        email = detail.get("email")
        if not instance_type:
            raise ValueError("Missing instanceType")

        create_instance = CreateInstanceForUser(
            compute=compute,
            repo=instance_repo,
            clock=clock,
            region=settings.aws_region,
        )
        handler = ProcessInstanceCreateRequested(create_instance=create_instance, request_repo=request_repo)
        handler.execute(
            user_id=user_id,
            request_id=request_id,
            email=str(email) if email else None,
            instance_type=instance_type,
            key_name=str(key_name) if key_name else None,
            ami_id=settings.ami_id,
        )
        return

    if detail_type == "InstancesTerminateRequested":
        instance_id = detail.get("instanceId")
        terminate_for_user = TerminateInstancesForUser(compute=compute, repo=instance_repo)
        terminate_single = TerminateSingleInstance(compute=compute, repo=instance_repo)
        handler = ProcessInstancesTerminateRequested(
            terminate_for_user=terminate_for_user,
            terminate_single=terminate_single,
            request_repo=request_repo,
        )
        handler.execute(
            user_id=user_id,
            request_id=request_id,
            instance_id=str(instance_id) if instance_id else None,
        )
        return

    # Ignore unrelated events
    return
