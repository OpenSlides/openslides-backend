from typing import Any, Dict, List, Tuple

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
from ..shared.exceptions import MissingPermission, PresenterException
from ..shared.filters import FilterOperator, Or
from ..shared.patterns import Collection, FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

search_users_by_name_email_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "search_users_by_name_email",
        "description": "get lists of id, first-, last-name and email for tuples of exact (username, emails)-tuples.",
        "properties": {
            "permission_scope": {
                "type": "array",
                "prefixItems": [
                    {
                        "enum": [1, 2, 3]
                    },  # Permission scopes Meeting, Committee, Organization
                    {"type": "number"},  # Id of object, 1 for organization
                ],
            },
            "search": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "prefixItems": [
                        {"type": "string"},  # username
                        {"type": "string"},  # email-adress
                    ],
                },
            },
        },
        "required": ["permission_scope"],
        "additionalProperties": False,
    }
)


@register_presenter("search_users_by_name_email")
class SearchUsersByNameEmail(BasePresenter):
    """
    Collects users with exect usernames or exact emails.
    """

    schema = search_users_by_name_email_schema

    def get_result(self) -> Any:
        self.check_permissions(self.data["permission_scope"])
        result: Dict[str, List[Tuple[int, str, str, str]]] = {}
        for search in self.data["search"]:
            if search[0] and search[1]:
                filter_ = Or(
                    FilterOperator("username", "=", search[0]),
                    FilterOperator("email", "=", search[1]),
                )
            elif search[0]:
                filter_ = FilterOperator("username", "=", search[0])
            elif search[1]:
                filter_ = FilterOperator("email", "=", search[1])
            else:
                continue
            instances = self.datastore.filter(
                Collection("user"), filter_, ["id", "first_name", "last_name", "email"]
            )

            result[f"{search[0]}/{search[1]}"] = [
                (
                    instance["id"],
                    instance.get("first_name", ""),
                    instance.get("last_name", ""),
                    instance.get("email", ""),
                )
                for instance in instances.values()
            ]
        return result

    def check_permissions(self, permission_scope: Tuple[int, int]) -> None:
        if (
            permission_scope[0] < UserScope.Meeting.value
            or permission_scope[0] > UserScope.Organization.value
            or permission_scope[1] < 1
        ):
            raise PresenterException(
                f"There is no valid PermissionScope given with {permission_scope[0]}/{permission_scope[1]}"
            )
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return
        if permission_scope[0] == UserScope.Organization.value:
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
        if permission_scope[0] == UserScope.Committee.value:
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                permission_scope[1],
            ):
                return
            else:
                raise MissingPermission(
                    {CommitteeManagementLevel.CAN_MANAGE: permission_scope[1]}
                )
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.User.CAN_MANAGE,
            permission_scope[1],
        ):
            return
        else:
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), permission_scope[1]),
                ["committee_id"],
            )
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                meeting.get("committee_id", 0),
            ):
                return
            raise MissingPermission({Permissions.User.CAN_MANAGE: permission_scope[1]})
