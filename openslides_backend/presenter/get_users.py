from operator import itemgetter
from typing import Any, Dict, List

import fastjsonschema

from ..services.datastore.deleted_models_behaviour import DeletedModelsBehaviour
from ..shared.exceptions import PresenterException
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
            "filter": {"type": ["string", "null"]},
        },
        "required": [],
        "additionalProperties": False,
    }
)

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
    "structure_level": "",
    "vote_weight": "",
}


@register_presenter("get_users")
class GetUsers(BasePresenter):
    """
    Gets all users and return some user_ids.
    """

    schema = get_users_schema

    def get_result(self) -> Any:
        criteria = self.get_and_check_criteria()
        users = self.get_all_users(criteria)
        users = self.filter_keyword(users)
        users = self.sort_users(users, criteria)
        users = self.paginate_users(users)
        return {"users": [user["id"] for user in users]}

    def get_and_check_criteria(self) -> List[str]:
        default_criteria = ["last_name", "first_name", "username"]
        criteria = self.data.get("sort_criteria", default_criteria)

        not_allowed = [crit for crit in criteria if crit not in ALLOWED]
        if not_allowed:
            raise PresenterException(f"Sort criteria '{not_allowed}' are not allowed")
        return criteria

    def get_all_users(self, criteria: List[str]) -> List[Dict[str, Any]]:
        fields = criteria[:]
        for name in ("username", "first_name", "last_name", "id"):
            if name not in fields:
                fields.append(name)

        return list(
            self.datastore.get_all(
                Collection("user"),
                fields,
                DeletedModelsBehaviour.NO_DELETED,
            ).values()
        )

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

    def sort_users(
        self, users: List[Dict[str, Any]], criteria: List[str]
    ) -> List[Dict[str, Any]]:
        for user in users:
            for crit in criteria:
                if user.get(crit) is None:
                    user[crit] = ALLOWED[crit]

        users.sort(key=itemgetter(*criteria), reverse=self.data.get("reverse", False))
        return users

    def paginate_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        start_index = self.data.get("start_index", 0)
        end_index = start_index + self.data.get("entries", 100)
        users = users[start_index:end_index]
        return users
