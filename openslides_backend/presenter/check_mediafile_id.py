from typing import Any, Dict

import fastjsonschema

from ..models.models import Mediafile
from ..permissions.management_levels import CommitteeManagementLevel
from ..permissions.permission_helper import (
    has_committee_management_level,
    has_perm,
    is_admin,
)
from ..permissions.permissions import Permissions
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection, FullQualifiedId
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

check_mediafile_id_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "check_mediafile_id data",
        "description": "Schema to validate the check_mediafile_id presenter data.",
        "properties": {"mediafile_id": required_id_schema},
        "required": ["mediafile_id"],
        "additionalProperties": False,
    }
)


@register_presenter("check_mediafile_id", csrf_exempt=True)
class CheckMediafileId(BasePresenter):
    """
    Check, if a mediafile can be accessed. Retrieve the filename, if access is granted.
    """

    schema = check_mediafile_id_schema

    def get_result(self) -> Any:
        mediafile = self.datastore.get(
            FullQualifiedId(Mediafile.collection, self.data["mediafile_id"]),
            mapped_fields=["filename", "is_directory"],
        )

        if not mediafile or mediafile.get("is_directory"):
            return {"ok": False}
        self.check_permissions()

        return {"ok": True, "filename": mediafile["filename"]}

    def check_permissions(self) -> None:
        mediafile = self.datastore.get(
            FullQualifiedId(Mediafile.collection, self.data["mediafile_id"]),
            [
                "meeting_id",
                "used_as_logo_$_in_meeting_id",
                "used_as_font_$_in_meeting_id",
                "projection_ids",
                "is_public",
                "inherited_access_group_ids",
            ],
        )
        meeting_id = mediafile.get("meeting_id")
        if not meeting_id:
            raise PermissionDenied("You are not allowed to see this mediafile.")

        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["enable_anonymous", "user_ids", "committee_id"],
        )
        # The user is admin of the meeting.
        if is_admin(self.datastore, self.user_id, meeting_id):
            return

        # The user can see the meeting and (used_as_logo_$_in_meeting_id
        #    or used_as_font_$_in_meeting_id is not empty)
        can_see_meeting = self.check_can_see_meeting(meeting)
        if can_see_meeting:
            if mediafile.get("used_as_logo_$_in_meeting_id") or mediafile.get(
                "used_as_font_$_in_meeting_id"
            ):
                return
        # The user has projector.can_see
        # and there exists a mediafile/projection_ids with
        # projection/current_projector_id set
        if has_perm(
            self.datastore, self.user_id, Permissions.Projector.CAN_SEE, meeting_id
        ):
            for projection_id in mediafile.get("projection_ids", []):
                projection = self.datastore.get(
                    FullQualifiedId(Collection("projection"), projection_id),
                    ["current_projector_id"],
                )
                if projection.get("current_projector_id"):
                    return
        # The user has mediafile.can_see and either:
        #  - mediafile/is_public is true, or
        #   - The user has groups in common with mediafile/inherited_access_group_ids
        if has_perm(
            self.datastore, self.user_id, Permissions.Mediafile.CAN_SEE, meeting_id
        ):
            if mediafile.get("is_public"):
                return
            inherited_access_group_ids = set(
                mediafile.get("inherited_access_group_ids", [])
            )
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), self.user_id),
                [f"group_${meeting_id}_ids"],
            )
            user_groups = set(user.get(f"group_${meeting_id}_ids", []))
            if inherited_access_group_ids & user_groups:
                return
        raise PermissionDenied("You are not allowed to see this mediafile.")

    def check_can_see_meeting(self, meeting: Dict[str, Any]) -> bool:
        """needs meeting to include enable_anonymous, user_ids, committee_id."""
        if meeting.get("enable_anonymous"):
            return True
        if self.user_id in meeting.get("user_ids", []):
            return True
        if meeting.get("committee_id"):
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                meeting["committee_id"],
            ):
                return True
        return False
