from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence


@dataclass(frozen=True)
class CreateInstanceSpec:
    instance_type: str
    ami_id: str | None
    key_name: str | None
    created_by_tag_value: str = "UnifiedLambda"


class ComputePort(Protocol):
    def create_instance(self, spec: CreateInstanceSpec) -> str: ...

    def terminate_instances(self, instance_ids: Sequence[str]) -> None: ...


@dataclass(frozen=True)
class InstanceItem:
    user_id: str
    instance_id: str
    created_at_iso: str
    region: str
    instance_type: str
    state: str
    email: str | None = None


class InstanceRepositoryPort(Protocol):
    def put(self, item: InstanceItem) -> None: ...

    def list_instance_ids_for_user(self, user_id: str) -> list[str]: ...

    def delete(self, user_id: str, instance_id: str) -> None: ...


class ClockPort(Protocol):
    def now_utc(self) -> datetime: ...


@dataclass(frozen=True)
class DomainEvent:
    source: str
    detail_type: str
    detail: dict


class EventBusPort(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


@dataclass(frozen=True)
class CreateRequestItem:
    user_id: str
    request_id: str
    requested_at_iso: str
    status: str  # PENDING | SUCCEEDED | FAILED
    action: str  # CREATE | DELETE_ONE | DELETE_ALL
    instance_type: str
    key_name: str | None
    email: str | None
    target_instance_id: str | None = None


@dataclass(frozen=True)
class RequestStatus:
    request_id: str
    status: str
    instance_id: str | None
    error: str | None
    terminated: list[str] | None = None


class RequestRepositoryPort(Protocol):
    def create(self, item: CreateRequestItem) -> None: ...

    def set_result(
        self,
        *,
        user_id: str,
        request_id: str,
        status: str,
        instance_id: str | None,
        error: str | None,
        terminated: list[str] | None,
    ) -> None: ...

    def get_status(self, *, user_id: str, request_id: str) -> RequestStatus | None: ...
