from typing import Any, Dict, List

import fastjsonschema
from datastore.shared.util import DeletedModelsBehaviour

from ..models.checker import Checker, CheckException
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
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

        if self.data.get("meeting_id"):
            meeting_ids = [self.data["meeting_id"]]
        else:
            meeting_ids = self.get_all_meeting_ids()
        errors: Dict[int, str] = {}
        for meeting_id in meeting_ids:
            export = export_meeting(self.datastore, meeting_id)
            checker = Checker(
                data=export,
                mode="internal",
                repair=True,
                fields_to_remove={
                    "motion": [
                        "origin_id",
                        "derived_motion_ids",
                        "all_origin_id",
                        "all_derived_motion_ids",
                    ]
                },
            )
            try:
                checker.run_check()
            except CheckException as ce:
                errors[meeting_id] = str(ce)
        if not errors:
            return {"ok": True, "errors": ""}
        return {"ok": False, "errors": self.gen_error_message(errors)}

    def get_all_meeting_ids(self) -> List[int]:
        meetings = self.datastore.get_all(
            "meeting", ["id"], DeletedModelsBehaviour.NO_DELETED
        ).values()
        return [meeting["id"] for meeting in meetings]

    def gen_error_message(self, errors: Dict[int, str]) -> str:
        buf = []
        for meeting_id in errors:
            buf.append(f"Meeting {meeting_id}")
            buf.append(errors[meeting_id])
        return "\n".join(buf)
