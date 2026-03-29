from __future__ import annotations

import boto3

from ...ports import CreateRequestItem, RequestRepositoryPort, RequestStatus


def _sk(request_id: str) -> str:
    return f"REQ#{request_id}"


class DynamoDbRequestRepository(RequestRepositoryPort):
    def __init__(self, *, region: str, table_name: str) -> None:
        self._region = region
        self._table_name = table_name

    def _table(self):
        ddb = boto3.resource("dynamodb", region_name=self._region)
        return ddb.Table(self._table_name)

    def create(self, item: CreateRequestItem) -> None:
        self._table().put_item(
            Item={
                "user_id": item.user_id,
                "instance_id": _sk(item.request_id),
                "item_type": "request",
                "request_id": item.request_id,
                "requested_at": item.requested_at_iso,
                "status": item.status,
                "action": item.action,
                "instance_type": item.instance_type,
                **({"key_name": item.key_name} if item.key_name else {}),
                **({"email": item.email} if item.email else {}),
                **({"target_instance_id": item.target_instance_id} if item.target_instance_id else {}),
            },
            ConditionExpression="attribute_not_exists(user_id) AND attribute_not_exists(instance_id)",
        )

    def set_result(
        self,
        *,
        user_id: str,
        request_id: str,
        status: str,
        instance_id: str | None,
        error: str | None,
        terminated: list[str] | None,
    ) -> None:
        expr_names = {"#s": "status"}
        expr_values: dict = {":status": status}
        updates = ["#s = :status"]

        if instance_id is not None:
            expr_names["#iid"] = "result_instance_id"
            expr_values[":iid"] = instance_id
            updates.append("#iid = :iid")

        if error is not None:
            expr_names["#err"] = "error"
            expr_values[":err"] = error
            updates.append("#err = :err")

        if terminated is not None:
            expr_names["#term"] = "terminated"
            expr_values[":term"] = list(terminated)
            updates.append("#term = :term")

        update_expr = "SET " + ", ".join(updates)

        self._table().update_item(
            Key={"user_id": user_id, "instance_id": _sk(request_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    def get_status(self, *, user_id: str, request_id: str) -> RequestStatus | None:
        resp = self._table().get_item(Key={"user_id": user_id, "instance_id": _sk(request_id)})
        item = resp.get("Item")
        if not item:
            return None
        return RequestStatus(
            request_id=request_id,
            status=str(item.get("status") or "UNKNOWN"),
            instance_id=item.get("result_instance_id"),
            error=item.get("error"),
            terminated=item.get("terminated"),
        )
