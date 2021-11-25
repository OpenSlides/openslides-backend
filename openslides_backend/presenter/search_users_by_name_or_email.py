from typing import Any, Dict, List, Union

import fastjsonschema

from ..action.actions.user.user_scope_permission_check_mixin import UserScope
from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ..permissions.permissions import Permissions
from ..shared.exceptions import ActionException, MissingPermission
from ..shared.filters import FilterOperator, Or
from ..shared.patterns import Collection, FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

search_users_by_name_or_email_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "search_users_by_name_or_email",
        "description": "get lists of id, first-, last-name and email for tuples of exact (username, emails)-tuples.",
        "properties": {
            "permission_type": {
                "type": "integer",
                "enum": [1, 2, 3],
            },  # 1=meeting, 2=committee, 3=organization
            "permission_id": {
                "type": "integer",
                "minimum": 1,
            },
            "search": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            },
        },
        "required": ["permission_type", "permission_id", "search"],
        "additionalProperties": False,
    }
)


@register_presenter("search_users_by_name_or_email")
class SearchUsersByNameEmail(BasePresenter):
    """
    Collects users with exect usernames or exact emails.
    """

    schema = search_users_by_name_or_email_schema

    def get_result(self) -> Any:
        self.check_permissions(self.data["permission_type"], self.data["permission_id"])
        result: Dict[str, List[Dict[str, Union[str, int]]]] = {}
        for search in self.data["search"]:
            username = search.get("username", "")
            email = search.get("email", "")
            if username and email:
                filter_ = Or(
                    FilterOperator("username", "=", username),
                    FilterOperator("email", "=", email),
                )
            elif username:
                filter_ = FilterOperator("username", "=", username)
            elif email:
                filter_ = FilterOperator("email", "=", email)
            else:
                continue
            instances = self.datastore.filter(
                Collection("user"), filter_, ["id", "first_name", "last_name", "email"]
            )

            result[f"{username}/{email}"] = [
                instance for instance in instances.values()
            ]
        return result

    def check_permissions(self, permission_type: int, permission_id: int) -> None:
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return
        if permission_type == UserScope.Organization:
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
        if permission_type == UserScope.Committee:
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                permission_id,
            ):
                return
            else:
                raise MissingPermission(
                    {CommitteeManagementLevel.CAN_MANAGE: permission_id}
                )
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.User.CAN_MANAGE,
            permission_id,
        ):
            return
        else:
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), permission_id),
                ["committee_id"],
            )
            if (committee_id := meeting.get("committee_id", 0)) < 1:
                raise ActionException(
                    f"Error in database: Meeting {permission_id} has no valid committee_id!"
                )
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                committee_id,
            ):
                return
            raise MissingPermission({Permissions.User.CAN_MANAGE: permission_id})
