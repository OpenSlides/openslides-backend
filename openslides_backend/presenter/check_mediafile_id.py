import mimetypes
from typing import Any

import fastjsonschema

from openslides_backend.action.mixins.meeting_user_helper import (
    get_groups_from_meeting_user,
)

from ..models.models import Mediafile, Meeting
from ..permissions.management_levels import CommitteeManagementLevel
from ..permissions.permission_helper import (
    has_committee_management_level,
    has_perm,
    is_admin,
)
from ..permissions.permissions import Permissions
from ..shared.exceptions import (
    AnonymousNotAllowed,
    DatastoreException,
    PermissionDenied,
)
from ..shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
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
        try:
            mediafile = self.datastore.get(
                fqid_from_collection_and_id(
                    Mediafile.collection, self.data["mediafile_id"]
                ),
                mapped_fields=[
                    "filename",
                    "is_directory",
                    "owner_id",
                    "token",
                    "mimetype",
                    "projection_ids",
                    "is_public",
                    "inherited_access_group_ids",
                ]
                + Meeting.reverse_logo_places()
                + Meeting.reverse_font_places(),
            )
        except DatastoreException:
            return {"ok": False}
        if not mediafile.get("owner_id") or mediafile.get("is_directory"):
            return {"ok": False}
        collection, id_ = mediafile["owner_id"].split(KEYSEPARATOR)
        self.check_permissions(mediafile, collection, int(id_))
        filename = mediafile.get("filename")
        if collection == "organization" and mediafile.get("token"):
            if not mediafile.get("mimetype"):
                return {"ok": False}
            extension = mimetypes.guess_extension(mediafile["mimetype"])
            if extension is None:
                return {"ok": False}
            filename = mediafile["token"] + extension
        if filename:
            return {"ok": True, "filename": filename}
        return {"ok": False}

    def check_permissions(
        self, mediafile: dict[str, Any], owner_collection: str, owner_id: int
    ) -> None:
        # Try to get the meeting id.
        if owner_collection == "organization":
            if not mediafile.get("token"):
                self.assert_not_anonymous()
            return
        assert owner_collection == "meeting"

        if not owner_id:
            raise PermissionDenied("You are not allowed to see this mediafile.")

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", owner_id),
            ["enable_anonymous", "user_ids", "committee_id"],
        )
        # The user is admin of the meeting.
        if is_admin(self.datastore, self.user_id, owner_id):
            return

        # The user can see the meeting and (used_as_logo_xxx_in_meeting_id
        #    or used_as_font_xxx_in_meeting_id is not empty)
        can_see_meeting = self.check_can_see_meeting(meeting)
        if can_see_meeting:
            if any(
                mediafile.get(field)
                for field in Meeting.reverse_logo_places()
                + Meeting.reverse_font_places()
            ):
                return
        # The user has projector.can_see
        # and there exists a mediafile/projection_ids with
        # projection/current_projector_id set
        if has_perm(
            self.datastore, self.user_id, Permissions.Projector.CAN_SEE, owner_id
        ):
            for projection_id in mediafile.get("projection_ids", []):
                projection = self.datastore.get(
                    fqid_from_collection_and_id("projection", projection_id),
                    ["current_projector_id"],
                )
                if projection.get("current_projector_id"):
                    return
        # The user has mediafile.can_see and either:
        #  - mediafile/is_public is true, or
        #   - The user has groups in common with mediafile/inherited_access_group_ids
        if has_perm(
            self.datastore, self.user_id, Permissions.Mediafile.CAN_SEE, owner_id
        ):
            if mediafile.get("is_public"):
                return
            inherited_access_group_ids = set(
                mediafile.get("inherited_access_group_ids", [])
            )
            user_groups = set(
                get_groups_from_meeting_user(self.datastore, owner_id, self.user_id)
            )
            if inherited_access_group_ids & user_groups:
                return
        raise PermissionDenied("You are not allowed to see this mediafile.")

    def check_can_see_meeting(self, meeting: dict[str, Any]) -> bool:
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

    def assert_not_anonymous(self) -> None:
        """
        Checks if the request user is the Anonymous and raises an error if it is.
        """
        if self.services.authentication().is_anonymous(self.user_id):
            raise AnonymousNotAllowed("check_mediafile_id")
