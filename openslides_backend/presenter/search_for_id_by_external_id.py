from typing import Any

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import MissingPermission
from ..shared.filters import FilterOperator
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

search_for_id_by_external_id_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "search for id by external id",
        "description": "search for id with collection and external_id",
        "properties": {
            "collection": {
                "type": "string",
                "enum": ["user", "committee", "meeting", "group"],
            },
            "external_id": {"type": "string"},
        },
        "required": ["collection", "external_id"],
        "additionalProperties": False,
    }
)


@register_presenter("search_for_id_by_external_id")
class SearchForIdByExternalId(BasePresenter):
    """
    Search the collection for a entry with external_id. If found just one,
    returns the id. If the collection is "user", search the saml_id.
    """

    schema = search_for_id_by_external_id_schema

    def get_result(self) -> Any:
        self.check_permissions()
        field_name = "external_id"
        if self.data["collection"] == "user":
            field_name = "saml_id"
        filter_ = FilterOperator(field_name, "=", self.data["external_id"])
        filtered = self.datastore.filter(
            self.data["collection"], filter_, ["id"]
        ).values()
        if len(filtered) == 1:
            return {"id": next(iter(filtered))["id"]}
        elif len(filtered) == 0:
            error = f"No item with '{self.data['external_id']}' was found."
        else:
            error = f"More then one item with '{self.data['external_id']}' were found."
        return {"id": None, "error": error}

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION)
