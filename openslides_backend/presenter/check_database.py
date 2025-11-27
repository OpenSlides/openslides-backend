from typing import Any

import fastjsonschema

from ..models.checker import Checker, CheckException, external_motion_fields
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..services.database.interface import Database
from ..shared.exceptions import PermissionDenied
from ..shared.export_helper import export_meeting
from ..shared.schema import optional_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

check_database_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "check database",
        "description": "check database",
        "properties": {
            "meeting_id": optional_id_schema,
        },
        "required": [],
        "additionalProperties": False,
    }
)


def check_meetings(datastore: Database, meeting_id: int | None) -> dict[int, str]:
    if meeting_id:
        meeting_ids = [meeting_id]
    else:
        meetings = datastore.get_all("meeting", ["id"]).values()
        meeting_ids = [meeting["id"] for meeting in meetings]

    errors: dict[int, str] = {}
    for meeting_id in meeting_ids:
        export = export_meeting(datastore, meeting_id, True, True)
        try:
            Checker(
                data=export,
                mode="internal",
                repair=True,
                fields_to_remove={
                    "motion": external_motion_fields,
                },
            ).run_check()
        except CheckException as ce:
            errors[meeting_id] = str(ce)
    return errors


@register_presenter("check_database")
class CheckDatabase(BasePresenter):
    """Check Database gets all non-deleted meetings, exports them,
    and check them with the checker."""

    schema = check_database_schema

    def get_result(self) -> Any:
        # check permissions
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            msg = "You are not allowed to perform presenter check_database."
            msg += f" Missing permission: {OrganizationManagementLevel.SUPERADMIN}"
            raise PermissionDenied(msg)

        errors = check_meetings(self.datastore, self.data.get("meeting_id"))
        if not errors:
            return {"ok": True, "errors": ""}
        return {"ok": False, "errors": self.gen_error_message(errors)}

    def gen_error_message(self, errors: dict[int, str]) -> str:
        buf = []
        for meeting_id in errors:
            buf.append(f"Meeting {meeting_id}")
            buf.append(errors[meeting_id])
        return "\n".join(buf)
