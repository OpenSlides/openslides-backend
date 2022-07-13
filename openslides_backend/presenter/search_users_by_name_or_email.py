from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple, Union

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
from ..shared.patterns import fqid_from_collection_and_id
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
        result: Dict[str, List[Dict[str, Union[str, int]]]] = defaultdict(list)
        filter_bulk_tuples: Set[Tuple[str, str]] = set()
        for search in self.data["search"]:
            if username := search.get("username"):
                filter_bulk_tuples.add(("username", username))
            if email := search.get("email"):
                filter_bulk_tuples.add(("email", email))
        if len(filter_bulk_tuples) == 0:
            return result
        filter_bulk = Or(
            *[FilterOperator(t[0], "~=", t[1]) for t in filter_bulk_tuples]
        )
        instances = self.datastore.filter(
            "user",
            filter_bulk,
            ["id", "username", "first_name", "last_name", "email"],
            lock_result=False,
        )
        userd: Dict[str, Set[int]] = defaultdict(set)
        emaild: Dict[str, Set[int]] = defaultdict(set)
        for instance in instances.values():
            userd[instance["username"].lower()].add(instance["id"])
            emaild[instance["email"].lower()].add(instance["id"])
        for search in self.data["search"]:
            username = search.get("username", "")
            email = search.get("email", "")
            user_ids: Set[int] = userd.get(username.lower(), set()).union(
                emaild.get(email.lower(), set())
            )
            result[f"{username}/{email}"] = [instances[user_id] for user_id in user_ids]
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
