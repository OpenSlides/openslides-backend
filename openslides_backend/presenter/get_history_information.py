from typing import Any, cast

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import PermissionDenied
from ..shared.schema import required_fqid_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_history_information_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_history_information data",
        "description": "Schema to validate the get_history_information presenter data.",
        "properties": {"fqid": required_fqid_schema},
        "required": ["fqid"],
        "additionalProperties": False,
    }
)


@register_presenter("get_history_information")
class GetHistoryInformation(BasePresenter):
    """
    Return all history information for one fqid.
    """

    schema = get_history_information_schema

    def get_result(self) -> Any:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            raise PermissionDenied("You are not a superadmin")

        fqid = self.data["fqid"]
        response = self.datastore.history_information([fqid])
        information = cast(list[dict[str, Any]], response.get(fqid, []))

        # get all users
        user_ids = {position["user_id"] for position in information}
        usernames = self.get_usernames(user_ids)
        for position in information:
            position["user"] = usernames[position["user_id"]]
            del position["user_id"]
        return information

    def get_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}

        response = self.datastore.get_many(
            [
                GetManyRequest(
                    collection="user",
                    ids=list(user_ids),
                    mapped_fields=["username"],
                )
            ],
            lock_result=False,
        )["user"]

        return {
            user_id: response.get(user_id, {}).get("username", "unknown user")
            for user_id in user_ids
        }
