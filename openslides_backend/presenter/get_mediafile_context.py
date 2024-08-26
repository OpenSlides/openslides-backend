from typing import Any

import fastjsonschema

from openslides_backend.shared.schema import id_list_schema

from ..models.models import Meeting
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level, has_perm
from ..permissions.permissions import Permissions
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import MissingPermission
from ..shared.patterns import KEYSEPARATOR
from ..shared.schema import schema_version
from ..shared.util import ONE_ORGANIZATION_FQID
from .base import BasePresenter
from .presenter import register_presenter

get_mediafile_context_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_mediafile_context",
        "description": "get mediafile ids context",
        "properties": {
            "mediafile_ids": id_list_schema,
        },
        "required": ["mediafile_ids"],
        "additionalProperties": False,
    }
)


@register_presenter("get_mediafile_context")
class GetMediafileContext(BasePresenter):
    """
    Collects context of the mediafile_ids, specifically in relation to the meetings.
    """

    schema = get_mediafile_context_schema
    logo_fields = Meeting.reverse_logo_places()
    font_fields = Meeting.reverse_font_places()
    projection_places = ["current", "preview", "history"]

    def get_result(self) -> Any:
        self.meeting_names: dict[int, str] = {}
        result: dict[int, Any] = {}
        gmr = GetManyRequest(
            "mediafile",
            self.data["mediafile_ids"],
            [
                "id",
                "owner_id",
                "published_to_meetings_in_organization_id",
                "meeting_mediafile_ids",
                "child_ids",
            ],
        )
        mediafiles = self.datastore.get_many([gmr]).get("mediafile", {})
        self.check_permissions(
            {mediafile["owner_id"] for mediafile in mediafiles.values()}
        )
        for id_, mediafile in mediafiles.items():
            result[id_] = mediafile_data = {
                "owner_id": mediafile["owner_id"],
                "published": mediafile.get("published_to_meetings_in_organization_id")
                == 1,
            }
            amount_and_meeting_data = self.get_children_amount_and_meeting_data(
                mediafile
            )
            (
                mediafile_data["children_amount"],
                mediafile_data["meetings_of_interest"],
            ) = amount_and_meeting_data
        return result

    def check_permissions(self, owner_ids: set[str]) -> None:
        if ONE_ORGANIZATION_FQID in owner_ids:
            if not has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            ):
                raise MissingPermission(
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                )
            owner_ids.remove(ONE_ORGANIZATION_FQID)
        for owner_id in owner_ids:
            _, id_str = owner_id.split(KEYSEPARATOR)
            id_ = int(id_str)
            if not has_perm(
                self.datastore, self.user_id, Permissions.Mediafile.CAN_MANAGE, id_
            ):
                raise MissingPermission(Permissions.Mediafile.CAN_MANAGE)

    def get_children_amount_and_meeting_data(
        self,
        mediafile: dict[str, Any] = {},
        meeting_mediafiles: dict[int, dict[str, Any]] = {},
    ) -> tuple[int, dict[int, dict[str, Any]]]:
        gmrs: list[GetManyRequest] = []
        meeting_ids = {
            m_mediafile["meeting_id"] for m_mediafile in meeting_mediafiles.values()
        }
        meeting_ids = meeting_ids.difference(self.meeting_names)
        projection_ids = {
            projection_id
            for m_mediafile in meeting_mediafiles.values()
            for projection_id in m_mediafile.get("projection_ids", [])
        }
        if meeting_mediafile_ids := mediafile.get("meeting_mediafile_ids"):
            gmrs.append(
                GetManyRequest(
                    "meeting_mediafile",
                    meeting_mediafile_ids,
                    [
                        "meeting_id",
                        "attachment_ids",
                        "projection_ids",
                        *self.logo_fields,
                        *self.font_fields,
                    ],
                )
            )
        if child_ids := mediafile.get("child_ids", []):
            gmrs.append(
                GetManyRequest(
                    "mediafile", child_ids, ["meeting_mediafile_ids", "child_ids"]
                )
            )
        number_of_children = len(child_ids)
        if len(meeting_ids):
            gmrs.append(GetManyRequest("meeting", list(meeting_ids), ["name"]))
        if len(projection_ids):
            gmrs.append(
                GetManyRequest(
                    "projection",
                    list(projection_ids),
                    [
                        "meeting_id",
                        "current_projector_id",
                        "history_projector_id",
                        "preview_projector_id",
                    ],
                )
            )
        if len(gmrs):
            data = self.datastore.get_many(gmrs)
        else:
            data = {}
        if meetings := data.get("meeting"):
            self.meeting_names.update(
                {
                    meeting_id: meeting["name"]
                    for meeting_id, meeting in meetings.items()
                }
            )
        meeting_data: dict[int, dict[str, Any]] = {}
        for meeting_mediafile in meeting_mediafiles.values():
            meeting_id = meeting_mediafile["meeting_id"]
            contains_attachment = len(meeting_mediafile.get("attachment_ids", [])) > 0
            contains_logo = any(
                meeting_mediafile.get(field, 0) > 0 for field in self.logo_fields
            )
            contains_font = any(
                meeting_mediafile.get(field, 0) > 0 for field in self.font_fields
            )
            contains_projection = {
                place: any(
                    projection["meeting_id"] == meeting_id
                    and projection.get(place + "_projector_id") is not None
                    for projection_id in projection_ids
                    if (projection := data.get("projection", {}).get(projection_id, {}))
                )
                for place in self.projection_places
            }
            if (
                contains_attachment
                or contains_logo
                or contains_font
                or any(contains_projection.values())
            ):
                meeting_data[meeting_id] = {
                    "name": self.meeting_names[meeting_id],
                    "holds_attachments": contains_attachment,
                    "holds_logos": contains_logo,
                    "holds_fonts": contains_font,
                    **{
                        "holds_" + place + "_projections": contains_projection[place]
                        for place in self.projection_places
                    },
                }
        if meeting_mediafiles := data.get("meeting_mediafile", {}):
            pass  # TODO: What here
        if children := data.get("mediafile", {}):
            for i, child in enumerate(children.values()):
                child_number_of_children, child_meeting_data = (
                    self.get_children_amount_and_meeting_data(
                        child, meeting_mediafiles if i == 0 else {}
                    )
                )
                self.merge_meeting_data(child_meeting_data, meeting_data)
                number_of_children += child_number_of_children
        elif meeting_mediafiles:
            child_number_of_children, child_meeting_data = (
                self.get_children_amount_and_meeting_data(
                    meeting_mediafiles=meeting_mediafiles
                )
            )
            self.merge_meeting_data(child_meeting_data, meeting_data)
            number_of_children += child_number_of_children
        return number_of_children, meeting_data

    def merge_meeting_data(
        self,
        merge_from: dict[int, dict[str, Any]],
        merge_into: dict[int, dict[str, Any]],
    ) -> None:
        for id_, date in merge_from.items():
            if id_ not in merge_into:
                merge_into[id_] = date
            else:
                for field in [
                    "holds_attachments",
                    "holds_logos",
                    "holds_fonts",
                    *[
                        "holds_" + place + "_projections"
                        for place in self.projection_places
                    ],
                ]:
                    merge_into[id_][field] = merge_into[id_][field] or date[field]
