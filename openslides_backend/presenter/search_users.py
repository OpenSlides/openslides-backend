from typing import Any

import fastjsonschema

from openslides_backend.shared.mixins.user_scope_mixin import UserScope

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
from ..shared.filters import And, Filter, FilterOperator, Or
from ..shared.patterns import fqid_from_collection_and_id
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

search_fields = [["username"], ["saml_id"], ["member_number"], ["first_name", "last_name", "email"]]
all_fields = [field for fields in search_fields for field in fields]

search_users_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "search_users",
        "properties": {
            "permission_type": {
                "type": "string",
                "enum": list(UserScope),
            },
            "permission_id": {
                "type": "integer",
                "minimum": 1,
            },
            "search": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {field: {"type": "string"} for field in all_fields},
                    "additionalProperties": False,
                },
            },
        },
        "required": ["permission_type", "permission_id", "search"],
        "additionalProperties": False,
    }
)


@register_presenter("search_users")
class SearchUsers(BasePresenter):
    """
    Matches users to the search criteria either by username or saml id or
    by exact match of first name, last name AND email.
    Returns a list of users for each search criteria in payload order.
    """

    schema = search_users_schema

    def get_result(self) -> list[list[dict[str, Any]]]:
        self.check_permissions(self.data["permission_type"], self.data["permission_id"])
        filters: set[Filter] = set()
        for search in self.data["search"]:
            # strip all fields and use "" if no value was given
            for field in all_fields:
                search[field] = search.get(field, "").strip().lower()
            for search_def in search_fields:
                if all(search.get(field) for field in search_def):
                    filters.add(
                        And(
                            self.get_filter(field, search[field])
                            for field in search_def
                        )
                    )
                    break

        if len(filters):
            # fetch result from db
            instances = self.datastore.filter(
                "user",
                Or(*filters),
                ["id"] + all_fields,
                lock_result=False,
            )
        else:
            instances = {}

        # match result to search criteria
        result = []
        for search in self.data["search"]:
            current_result = []
            for instance in instances.values():
                for search_def in search_fields:
                    if any(search[field] for field in search_def):
                        if all(
                            (instance.get(field) or "").lower() == search[field]
                            for field in search_def
                        ):
                            current_result.append(instance)
                        break
            result.append(current_result)
        return result

    def get_filter(self, field: str, value: str) -> Filter:
        return Or(
            [FilterOperator(field, "~=", value)]
            + ([FilterOperator(field, "=", None)] if not value else [])
        )

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
                fqid_from_collection_and_id("meeting", permission_id),
                ["committee_id"],
                lock_result=False,
            )
            if (committee_id := meeting.get("committee_id", 0)) < 1:
                raise PresenterException(
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
