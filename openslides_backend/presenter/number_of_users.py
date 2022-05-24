from typing import Any, cast

import fastjsonschema

from ..shared.filters import FilterOperator
from ..shared.patterns import FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

number_of_users_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "number_of_users",
        "description": "get if number of users are possible to add.",
        "properties": {"number_of_users_to_add_or_activate": {"type": "integer"}},
        "required": ["number_of_users_to_add_or_activate"],
        "additionalProperties": False,
    }
)


@register_presenter("number_of_users")
class NumberOfUsers(BasePresenter):
    """
    Returns if it possible to add or active number of users.
    """

    schema = number_of_users_schema

    def get_result(self) -> Any:
        organization = self.datastore.get(
            cast(FullQualifiedId, "organization/1"),
            ["limit_of_users"],
        )
        limit_of_users = organization.get("limit_of_users")
        if limit_of_users == 0:
            return {"possible": True}
        filter_ = FilterOperator("is_active", "=", True)
        count_of_users = self.datastore.count("user", filter_)
        if (
            count_of_users + self.data["number_of_users_to_add_or_activate"]
            > limit_of_users
        ):
            return {"possible": False}
        return {"possible": True}
