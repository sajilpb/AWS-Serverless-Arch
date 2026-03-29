from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .ports import (
    ClockPort,
    ComputePort,
    CreateInstanceSpec,
    CreateRequestItem,
    DomainEvent,
    EventBusPort,
    InstanceItem,
    InstanceRepositoryPort,
    RequestRepositoryPort,
    RequestStatus,
)


@dataclass(frozen=True)
class CreateInstanceResult:
    instance_id: str


class CreateInstanceForUser:
    def __init__(
        self,
        *,
        compute: ComputePort,
        repo: InstanceRepositoryPort,
        clock: ClockPort,
        region: str,
    ) -> None:
        self._compute = compute
        self._repo = repo
        self._clock = clock
        self._region = region

    def execute(
        self,
        *,
        user_id: str | None,
        email: str | None,
        instance_type: str,
        ami_id: str | None,
        key_name: str | None,
    ) -> CreateInstanceResult:
        instance_id = self._compute.create_instance(
            CreateInstanceSpec(instance_type=instance_type, ami_id=ami_id, key_name=key_name)
        )

        if user_id:
            created_at = self._clock.now_utc().isoformat() + "Z"
            self._repo.put(
                InstanceItem(
                    user_id=user_id,
                    instance_id=instance_id,
                    created_at_iso=created_at,
                    region=self._region,
                    instance_type=instance_type,
                    state="pending",
                    email=email,
                )
            )

        return CreateInstanceResult(instance_id=instance_id)


@dataclass(frozen=True)
class CreateRequestResult:
    request_id: str


class RequestInstanceCreation:
    def __init__(
        self,
        *,
        request_repo: RequestRepositoryPort,
        event_bus: EventBusPort,
        clock: ClockPort,
        event_source: str,
    ) -> None:
        self._request_repo = request_repo
        self._event_bus = event_bus
        self._clock = clock
        self._event_source = event_source

    def execute(
        self,
        *,
        user_id: str,
        email: str | None,
        instance_type: str,
        key_name: str | None,
    ) -> CreateRequestResult:
        request_id = str(uuid4())
        requested_at_iso = self._clock.now_utc().isoformat() + "Z"
        self._request_repo.create(
            CreateRequestItem(
                user_id=user_id,
                request_id=request_id,
                requested_at_iso=requested_at_iso,
                status="PENDING",
                action="CREATE",
                instance_type=instance_type,
                key_name=key_name,
                email=email,
            )
        )

        self._event_bus.publish(
            DomainEvent(
                source=self._event_source,
                detail_type="InstanceCreateRequested",
                detail={
                    "requestId": request_id,
                    "userId": user_id,
                    "email": email,
                    "instanceType": instance_type,
                    "keyName": key_name,
                },
            )
        )

        return CreateRequestResult(request_id=request_id)


class GetRequestStatus:
    def __init__(self, *, request_repo: RequestRepositoryPort) -> None:
        self._request_repo = request_repo

    def execute(self, *, user_id: str, request_id: str) -> RequestStatus | None:
        return self._request_repo.get_status(user_id=user_id, request_id=request_id)


class ProcessInstanceCreateRequested:
    def __init__(
        self,
        *,
        create_instance: CreateInstanceForUser,
        request_repo: RequestRepositoryPort,
    ) -> None:
        self._create_instance = create_instance
        self._request_repo = request_repo

    def execute(
        self,
        *,
        user_id: str,
        request_id: str,
        email: str | None,
        instance_type: str,
        key_name: str | None,
        ami_id: str | None,
    ) -> None:
        try:
            result = self._create_instance.execute(
                user_id=user_id,
                email=email,
                instance_type=instance_type,
                ami_id=ami_id,
                key_name=key_name,
            )
            self._request_repo.set_result(
                user_id=user_id,
                request_id=request_id,
                status="SUCCEEDED",
                instance_id=result.instance_id,
                error=None,
                terminated=None,
            )
        except Exception as e:
            self._request_repo.set_result(
                user_id=user_id,
                request_id=request_id,
                status="FAILED",
                instance_id=None,
                error=str(e),
                terminated=None,
            )
            raise


@dataclass(frozen=True)
class DeleteRequestResult:
    request_id: str


class RequestInstanceTermination:
    def __init__(
        self,
        *,
        request_repo: RequestRepositoryPort,
        event_bus: EventBusPort,
        clock: ClockPort,
        event_source: str,
    ) -> None:
        self._request_repo = request_repo
        self._event_bus = event_bus
        self._clock = clock
        self._event_source = event_source

    def execute(
        self,
        *,
        user_id: str,
        email: str | None,
        instance_id: str | None,
    ) -> DeleteRequestResult:
        request_id = str(uuid4())
        requested_at_iso = self._clock.now_utc().isoformat() + "Z"
        action = "DELETE_ONE" if instance_id else "DELETE_ALL"

        self._request_repo.create(
            CreateRequestItem(
                user_id=user_id,
                request_id=request_id,
                requested_at_iso=requested_at_iso,
                status="PENDING",
                action=action,
                instance_type="",
                key_name=None,
                email=email,
                target_instance_id=instance_id,
            )
        )

        self._event_bus.publish(
            DomainEvent(
                source=self._event_source,
                detail_type="InstancesTerminateRequested",
                detail={
                    "requestId": request_id,
                    "userId": user_id,
                    "email": email,
                    "instanceId": instance_id,
                },
            )
        )

        return DeleteRequestResult(request_id=request_id)


class ProcessInstancesTerminateRequested:
    def __init__(
        self,
        *,
        terminate_for_user: TerminateInstancesForUser,
        terminate_single: TerminateSingleInstance,
        request_repo: RequestRepositoryPort,
    ) -> None:
        self._terminate_for_user = terminate_for_user
        self._terminate_single = terminate_single
        self._request_repo = request_repo

    def execute(self, *, user_id: str, request_id: str, instance_id: str | None) -> None:
        try:
            if instance_id:
                result = self._terminate_single.execute(instance_id=instance_id, user_id=user_id)
            else:
                result = self._terminate_for_user.execute(user_id=user_id)

            self._request_repo.set_result(
                user_id=user_id,
                request_id=request_id,
                status="SUCCEEDED",
                instance_id=instance_id,
                error=None,
                terminated=result.terminated,
            )
        except Exception as e:
            self._request_repo.set_result(
                user_id=user_id,
                request_id=request_id,
                status="FAILED",
                instance_id=instance_id,
                error=str(e),
                terminated=None,
            )
            raise


@dataclass(frozen=True)
class TerminateResult:
    terminated: list[str]


class TerminateInstancesForUser:
    def __init__(self, *, compute: ComputePort, repo: InstanceRepositoryPort) -> None:
        self._compute = compute
        self._repo = repo

    def execute(self, *, user_id: str) -> TerminateResult:
        instance_ids = self._repo.list_instance_ids_for_user(user_id)
        if not instance_ids:
            return TerminateResult(terminated=[])

        self._compute.terminate_instances(instance_ids)
        for iid in instance_ids:
            try:
                self._repo.delete(user_id, iid)
            except Exception:
                # repository deletion failures shouldn't hide termination success
                pass

        return TerminateResult(terminated=list(instance_ids))


class TerminateSingleInstance:
    def __init__(self, *, compute: ComputePort, repo: InstanceRepositoryPort | None = None) -> None:
        self._compute = compute
        self._repo = repo

    def execute(self, *, instance_id: str, user_id: str | None) -> TerminateResult:
        self._compute.terminate_instances([instance_id])
        if self._repo and user_id:
            try:
                self._repo.delete(user_id, instance_id)
            except Exception:
                pass
        return TerminateResult(terminated=[instance_id])
