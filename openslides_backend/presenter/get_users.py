from operator import itemgetter
from typing import Any

import fastjsonschema
from datastore.shared.util import DeletedModelsBehaviour

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import MissingPermission
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

# The values are the default values for None.
ALLOWED = {
    "first_name": "",
    "last_name": "",
    "username": "",
    "title": "",
    "is_active": False,
    "is_physical_person": False,
    "email": "",
    "last_email_send": 0,
    "is_demo_user": False,
    "number": "",
    "vote_weight": "",
}

get_users_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_users",
        "description": "get user ids data",
        "properties": {
            "start_index": {"type": "integer"},
            "entries": {"type": "integer"},
            "sort_criteria": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(ALLOWED.keys()),
                },
            },
            "reverse": {"type": "boolean"},
            "filter": {"type": ["string", "null"]},
        },
        "required": [],
        "additionalProperties": False,
    }
)


@register_presenter("get_users")
class GetUsers(BasePresenter):
    """
    Gets all users and return some user_ids.
    """

    schema = get_users_schema

    def get_result(self) -> Any:
        self.check_permissions()
        criteria = self.get_criteria()
        users = self.get_all_users(criteria)
        users = self.filter_keyword(users)
        users = self.sort_users(users, criteria)
        users = self.paginate_users(users)
        return {"users": [user["id"] for user in users]}

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)

    def get_criteria(self) -> list[str]:
        default_criteria = ["last_name", "first_name", "username"]
        criteria = self.data.get("sort_criteria", default_criteria)
        return criteria

    def get_all_users(self, criteria: list[str]) -> list[dict[str, Any]]:
        fields = criteria[:]
        for name in ("username", "first_name", "last_name", "id"):
            if name not in fields:
                fields.append(name)

        return list(
            self.datastore.get_all(
                "user",
                fields,
                DeletedModelsBehaviour.NO_DELETED,
            ).values()
        )

    def _check_name(self, user: dict[str, Any], name: str) -> bool:
        return user.get(name) is not None and self.data["filter"] in user[name]

    def filter_keyword(self, users: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.data.get("filter"):
            users = [
                user
                for user in users
                if self._check_name(user, "username")
                or self._check_name(user, "first_name")
                or self._check_name(user, "last_name")
            ]
        return users

    def sort_users(
        self, users: list[dict[str, Any]], criteria: list[str]
    ) -> list[dict[str, Any]]:
        for user in users:
            for crit in criteria:
                if user.get(crit) is None:
                    user[crit] = ALLOWED[crit]

        users.sort(key=itemgetter(*criteria), reverse=self.data.get("reverse", False))
        return users

    def paginate_users(self, users: list[dict[str, Any]]) -> list[dict[str, Any]]:
        start_index = self.data.get("start_index", 0)
        end_index = start_index + self.data.get("entries", 100)
        users = users[start_index:end_index]
        return users
