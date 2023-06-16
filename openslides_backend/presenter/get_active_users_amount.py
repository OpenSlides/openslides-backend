from typing import Any

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import MissingPermission
from ..shared.functions.count_users_for_limit import count_users_for_limit
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_active_users_amount_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_users",
        "description": "get user ids data",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
)


@register_presenter("get_active_users_amount")
class GetActiveUsersAmount(BasePresenter):
    """
    Get number of all users
    """

    schema = get_active_users_amount_schema

    def get_result(self) -> Any:
        self.check_permissions()
        return {"active_users_amount": count_users_for_limit(self.datastore)}

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
