from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserIdentity:
    sub: str | None
    email: str | None


@dataclass(frozen=True)
class InstanceRecord:
    user_id: str
    instance_id: str
    created_at: datetime
    region: str
    instance_type: str
    state: str
    email: str | None = None
