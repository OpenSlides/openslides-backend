from typing import Any

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import MissingPermission
from ..shared.filters import And, FilterOperator
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
                "enum": ["committee", "meeting", "group"],
            },
            "external_id": {"type": "string"},
            "context_id": {"type": "integer"},
        },
        "required": ["collection", "external_id", "context_id"],
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
        context_field_map = {
            "group": "meeting_id",
            "meeting": "committee_id",
            "committee": "organization_id",
        }
        filter_ = And(
            FilterOperator("external_id", "=", self.data["external_id"]),
            FilterOperator(
                context_field_map[self.data["collection"]], "=", self.data["context_id"]
            ),
        )
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
