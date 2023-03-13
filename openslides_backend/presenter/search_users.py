from typing import Any, Dict, List, Set, Tuple

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

user_match_fields = ["username", "first_name", "last_name", "email"]
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
                    "properties": {
                        field: {"type": "string"} for field in user_match_fields
                    },
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
    Matches users to the search criteria either by username or by exact match of first name, last
    name AND email. Returns a list of users for each search criteria in payload order.
    """

    schema = search_users_schema

    def get_result(self) -> List[List[Dict[str, Any]]]:
        self.check_permissions(self.data["permission_type"], self.data["permission_id"])
        filter_tuples: Set[Tuple[str, ...]] = set()
        for search in self.data["search"]:
            # strip all fields and use "" if no value was given
            for field in user_match_fields:
                search[field] = search.get(field, "").strip().lower()
            if search["username"]:
                # if a username is given, match only by username
                filter_tuples.add((search["username"],))
            elif search["first_name"] or search["last_name"] or search["email"]:
                # otherwise ALL of first name, last name and email must match
                filter_tuples.add(
                    (search["first_name"], search["last_name"], search["email"])
                )

        if len(filter_tuples):
            # fetch result from db
            filters: List[Filter] = [
                FilterOperator("username", "~=", t[0])
                if len(t) == 1
                else And(
                    FilterOperator("first_name", "~=", t[0]),
                    FilterOperator("last_name", "~=", t[1]),
                    FilterOperator("email", "~=", t[2]),
                )
                for t in filter_tuples
            ]
            instances = self.datastore.filter(
                "user",
                Or(*filters),
                ["id", "username", "first_name", "last_name", "email"],
                lock_result=False,
            )
        else:
            instances = {}

        # match result to search criteria
        result = []
        for search in self.data["search"]:
            current_result = []
            for instance in instances.values():
                if (instance.get("username", "").lower() == search["username"]) or (
                    instance.get("first_name", "").lower() == search["first_name"]
                    and instance.get("last_name", "").lower() == search["last_name"]
                    and instance.get("email", "").lower() == search["email"]
                ):
                    current_result.append(instance)
            result.append(current_result)
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
