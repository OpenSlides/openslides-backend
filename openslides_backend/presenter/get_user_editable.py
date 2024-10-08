from typing import Any

import fastjsonschema

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import (
    ActionException,
    MissingPermission,
    PermissionDenied,
    PresenterException,
)
from openslides_backend.shared.mixins.user_create_update_permissions_mixin import (
    CreateUpdatePermissionsMixin,
)
from openslides_backend.shared.schema import id_list_schema, str_list_schema

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
            "fields": str_list_schema,
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
    name = "get_user_editable"
    permission = Permissions.User.CAN_MANAGE

    def get_result(self) -> Any:
        result: dict[str, Any] = {}
        if not self.data["fields"]:
            raise PresenterException(
                "Need at least one field name to check editability."
            )
        instance = {field_name: "" for field_name in self.data["fields"]}
        for user_id in self.data["user_ids"]:
            instance.update({"id": user_id})
            result[str(user_id)] = {}
            try:
                self.check_permissions(instance)
                result[str(user_id)]["editable"] = True
            except (PermissionDenied, MissingPermission, ActionException) as e:
                result[str(user_id)]["editable"] = False
                result[str(user_id)]["message"] = e.message
        return result
