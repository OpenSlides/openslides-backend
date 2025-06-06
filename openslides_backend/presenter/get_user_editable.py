from collections import defaultdict
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
        "required": ["user_ids", "fields"],
        "additionalProperties": False,
    }
)


@register_presenter("get_user_editable")
class GetUserEditable(CreateUpdatePermissionsMixin, BasePresenter):
    """
    Checks for each given user whether the given fields are editable by calling user on a per payload group basis.
    """

    schema = get_user_editable_schema
    name = "get_user_editable"
    permission = Permissions.User.CAN_MANAGE

    def get_result(self) -> Any:
        if not self.data["fields"]:
            raise PresenterException(
                "Need at least one field name to check editability."
            )
        reversed_field_rights = {
            field: group
            for group, fields in self.field_rights.items()
            for field in fields
        }
        one_field_per_group = {
            group_fields[0]
            for field_name in self.data["fields"]
            for group_fields in self.field_rights.values()
            if field_name in group_fields
        }
        result: defaultdict[str, dict[str, tuple[bool, str]]] = defaultdict(dict)
        for user_id in self.data["user_ids"]:
            result[str(user_id)] = {}
            groups_editable = {}
            for field_name in one_field_per_group:
                try:
                    self.check_permissions({"id": user_id, field_name: None})
                    groups_editable[reversed_field_rights[field_name]] = (True, "")
                except (PermissionDenied, MissingPermission, ActionException) as e:
                    groups_editable[reversed_field_rights[field_name]] = (
                        False,
                        e.message,
                    )
            result[str(user_id)].update(
                {
                    data_field_name: groups_editable[
                        reversed_field_rights[data_field_name]
                    ]
                    for data_field_name in self.data["fields"]
                }
            )
        return result
