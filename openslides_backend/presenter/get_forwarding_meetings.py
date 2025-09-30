from typing import Any

import fastjsonschema

from ..permissions.permission_helper import has_perm
from ..permissions.permissions import Permissions
from ..shared.exceptions import PermissionDenied, PresenterException
from ..shared.patterns import fqid_from_collection_and_id
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_forwarding_meetings_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_forwarding_meetings",
        "description": "get forwarding meetings",
        "properties": {
            "meeting_id": required_id_schema,
            "for_agenda": {"type": "boolean"},
        },
        "required": ["meeting_id"],
    }
)


@register_presenter("get_forwarding_meetings")
class GetForwardingMeetings(BasePresenter):
    """
    Get forwarded meetings.
    """

    schema = get_forwarding_meetings_schema

    def get_result(self) -> Any:
        # check permission
        for_agenda = self.data.pop("for_agenda", False)
        perm = (
            Permissions.AgendaItem.CAN_FORWARD
            if for_agenda
            else Permissions.Motion.CAN_FORWARD
        )
        collection = "agenda_item" if for_agenda else "motion"
        field = (
            "forward_agenda_to_committee_ids"
            if for_agenda
            else "forward_to_committee_ids"
        )
        if not has_perm(
            self.datastore,
            self.user_id,
            perm,
            self.data["meeting_id"],
        ):
            msg = f"You are not allowed to perform presenter get_forwarding_meetings for {collection}"
            msg += f" Missing permission: {perm}"
            raise PermissionDenied(msg)

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", self.data["meeting_id"]),
            ["committee_id", "is_active_in_organization_id", "name"],
        )
        if not meeting.get("is_active_in_organization_id"):
            raise PresenterException(
                f"Your sender meeting is an archived meeting, which can not forward {collection}s."
            )

        committee = self.datastore.get(
            fqid_from_collection_and_id("committee", meeting["committee_id"]),
            [field],
        )

        result = []
        for forward_to_committee_id in committee.get(field, []):
            forward_to_committee = self.datastore.get(
                fqid_from_collection_and_id("committee", forward_to_committee_id),
                ["meeting_ids", "name", "default_meeting_id"],
            )

            meeting_result = []
            for meeting_id2 in forward_to_committee.get("meeting_ids", []):
                meeting2 = self.datastore.get(
                    fqid_from_collection_and_id("meeting", meeting_id2),
                    ["name", "is_active_in_organization_id", "start_time", "end_time"],
                )
                if meeting2.get("is_active_in_organization_id"):
                    meeting_result.append(
                        {
                            "id": meeting_id2,
                            "name": meeting2.get("name", ""),
                            "start_time": meeting2.get("start_time"),
                            "end_time": meeting2.get("end_time"),
                        }
                    )
            if meeting_result:
                result.append(
                    {
                        "id": forward_to_committee_id,
                        "name": forward_to_committee.get("name", ""),
                        "meetings": meeting_result,
                        "default_meeting_id": forward_to_committee.get(
                            "default_meeting_id"
                        ),
                    }
                )
        return result
