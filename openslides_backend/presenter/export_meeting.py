from typing import Any

import fastjsonschema

from migrations import get_backend_migration_index

from ..action.actions.meeting.export_helper import export_meeting
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import PermissionDenied
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

export_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "export meeting",
        "description": "export meeting",
        "properties": {
            "meeting_id": required_id_schema,
        },
    }
)


@register_presenter("export_meeting")
class Export(BasePresenter):
    """
    Export meeting presenter.
    It calls the export meeting function and should be used by the superadmin.
    """

    schema = export_meeting_schema

    def get_result(self) -> Any:
        # check permissions
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            msg = "You are not allowed to perform presenter export_meeting."
            msg += f" Missing permission: {OrganizationManagementLevel.SUPERADMIN}"
            raise PermissionDenied(msg)
        export_data = export_meeting(self.datastore, self.data["meeting_id"])
        export_data["_migration_index"] = get_backend_migration_index()
        return export_data
