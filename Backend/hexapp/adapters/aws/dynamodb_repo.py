from __future__ import annotations

import boto3
from boto3.dynamodb.conditions import Key

from ...ports import InstanceItem, InstanceRepositoryPort


class DynamoDbInstanceRepository(InstanceRepositoryPort):
    def __init__(self, *, region: str, table_name: str) -> None:
        self._region = region
        self._table_name = table_name

    def _table(self):
        ddb = boto3.resource("dynamodb", region_name=self._region)
        return ddb.Table(self._table_name)

    def put(self, item: InstanceItem) -> None:
        self._table().put_item(
            Item={
                "user_id": item.user_id,
                "instance_id": item.instance_id,
                "item_type": "instance",
                "created_at": item.created_at_iso,
                "region": item.region,
                "instance_type": item.instance_type,
                "state": item.state,
                **({"email": item.email} if item.email else {}),
            }
        )

    def list_instance_ids_for_user(self, user_id: str) -> list[str]:
        resp = self._table().query(KeyConditionExpression=Key("user_id").eq(user_id))
        items = resp.get("Items", []) or []
        instance_ids: list[str] = []
        for it in items:
            iid = it.get("instance_id")
            if not iid:
                continue
            # The table may contain other item types (e.g., request tracking).
            item_type = it.get("item_type")
            if item_type == "instance" or str(iid).startswith("i-"):
                instance_ids.append(str(iid))
        return instance_ids

    def delete(self, user_id: str, instance_id: str) -> None:
        self._table().delete_item(Key={"user_id": user_id, "instance_id": instance_id})
