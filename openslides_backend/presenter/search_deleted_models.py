from typing import Any, List

import fastjsonschema
from datastore.shared.util import DeletedModelsBehaviour

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import PermissionDenied
from ..shared.filters import And, Filter, FilterOperator, Or
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "properties": {
            "collection": {"type": "string"},
            "filter_string": {"type": "string"},
            "meeting_id": {"type": "integer", "minimum": 1},
        },
        "required": ["collection", "filter_string"],
        "additionalProperties": False,
    }
)


search_fields = {
    "assignment": ["title"],
    "motion": ["number", "title"],
    "user": [
        "username",
        "first_name",
        "last_name",
        "title",
        "pronoun",
        "structure_level",
        "number",
        "email",
    ],
}


@register_presenter("search_deleted_models")
class SearchDeletedModels(BasePresenter):
    """
    Searches all deleted models of the given collection for a given filter string.
    """

    schema = schema

    def get_result(self) -> Any:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            raise PermissionDenied("You are not a superadmin")

        collection = self.data["collection"]
        meeting_id = self.data["meeting_id"]
        filters: List[Filter] = []
        for search_field in search_fields[collection]:
            filters.append(
                FilterOperator(search_field, "%=", self.data["filter_string"])
            )
            filter: Filter
        if len(filters) > 1:
            filter = Or(*filters)
        else:
            filter = filters[0]

        if collection == "user":
            filter = And(
                filter,
                FilterOperator(f"group_${meeting_id}_ids", "!=", None),
                FilterOperator(f"group_${meeting_id}_ids", "!=", []),
            )
        else:
            filter = And(filter, FilterOperator("meeting_id", "=", meeting_id))
        result = self.datastore.filter(
            collection,
            filter,
            ["id"] + search_fields[collection],
            DeletedModelsBehaviour.ONLY_DELETED,
            lock_result=False,
            use_changed_models=False,
        )

        return result
