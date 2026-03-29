from __future__ import annotations

import boto3

from ...ports import DomainEvent, EventBusPort


class EventBridgeBusAdapter(EventBusPort):
    def __init__(self, *, region: str) -> None:
        self._region = region

    def publish(self, event: DomainEvent) -> None:
        client = boto3.client("events", region_name=self._region)
        client.put_events(
            Entries=[
                {
                    "Source": event.source,
                    "DetailType": event.detail_type,
                    "Detail": __import__("json").dumps(event.detail),
                }
            ]
        )
