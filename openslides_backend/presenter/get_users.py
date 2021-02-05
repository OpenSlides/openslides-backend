from operator import itemgetter
from typing import Any, Dict, List, Optional

import fastjsonschema

from ..services.datastore.deleted_models_behaviour import DeletedModelsBehaviour
from ..shared.patterns import Collection
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

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
                "item": {
                    "type": "string",
                    "enum": ["username", "first_name", "last_name"],
                },
            },
            "reverse": {"type": "boolean"},
            "include_temporary": {"type": "boolean"},
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
        users = self.get_all_users()
        users = self.filter_temp_users(users)
        users = self.filter_keyword(users)
        users = self.sort_users(users)
        users = self.paginate_users(users)
        return {"users": [user["id"] for user in users]}

    def get_all_users(self) -> List[Dict[str, Any]]:
        return list(
            self.datastore.get_all(
                Collection("user"),
                ["id", "username", "first_name", "last_name", "meeting_id"],
                DeletedModelsBehaviour.NO_DELETED,
            ).values()
        )

    def filter_temp_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        if not self.data.get("include_temporary", False):
            users = [user for user in users if user.get("meeting_id") is None]
        return users

    def _check_name(self, user: Dict[str, Any], name: str) -> bool:
        return user.get(name) is not None and self.data["filter"] in user[name]

    def filter_keyword(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.data.get("filter"):
            users = [
                user
                for user in users
                if self._check_name(user, "username")
                or self._check_name(user, "first_name")
                or self._check_name(user, "last_name")
            ]
        return users

    def _str_if_None(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return value

    def sort_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        users = [
            {
                "username": self._str_if_None(user.get("username")),
                "id": user["id"],
                "first_name": self._str_if_None(user.get("first_name")),
                "last_name": self._str_if_None(user.get("last_name")),
            }
            for user in users
        ]
        default_criteria = ["last_name", "first_name", "username"]
        criteria = self.data.get("sort_criteria", default_criteria)
        users.sort(key=itemgetter(*criteria), reverse=self.data.get("reverse", False))
        return users

    def paginate_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        start_index = self.data.get("start_index", 0)
        end_index = start_index + self.data.get("entries", 100)
        users = users[start_index:end_index]
        return users
