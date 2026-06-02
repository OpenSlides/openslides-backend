from typing import Any

import fastjsonschema

from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import PermissionDenied, PresenterException
from ..shared.export_helper import export_meeting
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
            "old_db_compatibility": {"type": "boolean"},
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
        export_data = export_meeting(
            self.datastore,
            self.data["meeting_id"],
            transform_datetime_decimal=True,
            datetime_to_unix=self.data.get("old_db_compatibility"),
        )
        if id_ := next(
            (
                id_
                for id_, meeting in export_data["meeting"].items()
                if meeting.get("locked_from_inside")
            ),
            None,
        ):
            raise PresenterException(f"Cannot export: meeting {id_} is locked.")
        self.exclude_organization_tags_and_default_meeting_for_committee(export_data)
        if self.data.get("old_db_compatibility"):
            self.add_missing_mm_inherited_access_group_ids(export_data)
        return export_data

    def exclude_organization_tags_and_default_meeting_for_committee(
        self, export_data: dict[str, Any]
    ) -> None:
        self.get_meeting_from_json(export_data).pop("organization_tag_ids", None)
        self.get_meeting_from_json(export_data).pop(
            "default_meeting_for_committee_id", None
        )

    def add_missing_mm_inherited_access_group_ids(
        self, export_data: dict[str, Any]
    ) -> None:
        if "meeting_mediafile" not in export_data:
            return
        for meeting_mediafile_data in export_data["meeting_mediafile"].values():
            if "inherited_access_group_ids" not in meeting_mediafile_data:
                meeting_mediafile_data["inherited_access_group_ids"] = []

    def get_meeting_from_json(self, export_data: Any) -> Any:
        key = next(iter(export_data["meeting"]))
        return export_data["meeting"][key]
