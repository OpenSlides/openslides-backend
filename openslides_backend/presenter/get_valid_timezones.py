from typing import Any

import fastjsonschema
from psycopg import sql

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level, has_perm
from ..permissions.permissions import Permissions
from ..shared.exceptions import MissingPermission
from ..shared.patterns import fqid_from_collection_and_id
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_valid_timezones_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get valid timezones",
        "description": "get valid timezones",
        "properties": {},
    }
)


@register_presenter("get_valid_timezones")
class GetValidTimezones(BasePresenter):
    """
    Returns all timezones allowed by the database.
    """

    schema = get_valid_timezones_schema

    def get_result(self) -> Any:
        self.check_permissions()
        timezones = self.datastore.execute_custom_select(
            sql.SQL("name, abbrev FROM pg_timezone_names")
        )
        return {tz["name"]: tz["abbrev"] for tz in timezones}

    def check_permissions(self) -> None:
        if not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            user_data = self.datastore.get(
                fqid_from_collection_and_id("user", self.user_id),
                ["committee_management_ids", "meeting_ids"],
            )
            if not user_data.get("committee_management_ids") and not any(
                has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.Meeting.CAN_MANAGE_SETTINGS,
                    meeting_id,
                )
                for meeting_id in user_data.get("meeting_ids", [])
            ):
                raise MissingPermission(Permissions.Meeting.CAN_MANAGE_SETTINGS)
