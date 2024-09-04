from typing import Any

import fastjsonschema

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import MissingPermission, PermissionDenied
# from openslides_backend.action.actions.user.create_update_permissions_mixin import CreateUpdatePermissionsMixin
from openslides_backend.shared.mixins.user_create_update_permissions_mixin import (
    CreateUpdatePermissionsMixin,
)
from openslides_backend.shared.schema import id_list_schema

from ..shared.patterns import fqid_from_collection_and_id
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_user_editable_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_user_editable",
        "description": "get user editable",
        "properties": {
            "user_ids": id_list_schema,
        },
        "required": ["user_ids"],
        "additionalProperties": False,
    }
)


@register_presenter("get_user_editable")
class GetUserEditable(CreateUpdatePermissionsMixin, BasePresenter):
    """
    Checks for each user whether it is editable by calling user.
    """

    schema = get_user_editable_schema
    permission = Permissions.User.CAN_MANAGE

    def get_result(self) -> Any:
        result: dict[str, Any] = {}
        user_ids = self.data["user_ids"]
        # result["message"] = ""
        for user_id in user_ids:
            instance = self.datastore.get(
                fqid_from_collection_and_id("user", user_id),
                [
                    "id",
                    "meeting_user_ids",
                    "meeting_id",
                    "committee_management_ids",
                    "organization_management_level",
                ],
                lock_result=False,
            )
            result[str(user_id)] = {}
            try:
                if self.check_permissions(instance):
                    result[str(user_id)]["editable"] = True
                else:
                    result[str(user_id)]["editable"] = False
            except (PermissionDenied, MissingPermission) as e:
                result[str(user_id)]["editable"] = False
                result[str(user_id)]["message"] = e.message

                # result["message"] += e.message
        return result
