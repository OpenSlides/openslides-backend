from typing import Any

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import MissingPermission
from ..shared.filters import FilterOperator
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
    Get number of all users with is_active == True.
    """

    schema = get_active_users_amount_schema

    def get_result(self) -> Any:
        self.check_permissions()
        amount = self.get_amount()
        return {"active_users_amount": amount}

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)

    def get_amount(self) -> int:
        filter_ = FilterOperator("is_active", "=", True)
        return self.datastore.count("user", filter_)
