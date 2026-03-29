from __future__ import annotations

from datetime import datetime, timezone

from ...ports import ClockPort


class UtcClock(ClockPort):
    def now_utc(self) -> datetime:
        return datetime.now(tz=timezone.utc).replace(tzinfo=None)
