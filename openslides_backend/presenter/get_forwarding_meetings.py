from typing import Any

import fastjsonschema

from ..permissions.permission_helper import has_perm
from ..permissions.permissions import Permissions
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection, FullQualifiedId
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
        },
    }
)


@register_presenter("get_forwarding_meetings")
class GetForwardingMeetings(BasePresenter):
    """
    Get forwared meetings.
    """

    schema = get_forwarding_meetings_schema

    def get_result(self) -> Any:
        # check permission
        if not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_MANAGE,
            self.data["meeting_id"],
        ):
            msg = "You are not allowed to perform persenter get_forwarding_meetings"
            msg += f" Missing permission: {Permissions.Motion.CAN_MANAGE}"
            raise PermissionDenied(msg)

        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), self.data["meeting_id"]),
            ["committee_id"],
        )
        if not meeting.get("committee_id"):
            return []
        committee = self.datastore.get(
            FullQualifiedId(Collection("committee"), meeting["committee_id"]),
            ["forward_to_committee_ids"],
        )

        result = []
        for forward_to_committee_id in committee.get("forward_to_committee_ids", []):
            forward_to_committee = self.datastore.get(
                FullQualifiedId(Collection("committee"), forward_to_committee_id),
                ["meeting_ids", "name"],
            )

            meeting_result = []
            for meeting_id2 in forward_to_committee.get("meeting_ids", []):
                if not has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.Motion.CAN_CREATE,
                    meeting_id2,
                ):
                    continue
                meeting2 = self.datastore.get(
                    FullQualifiedId(Collection("meeting"), meeting_id2), ["name"]
                )
                meeting_result.append(
                    {"id": meeting_id2, "name": meeting2.get("name", "")}
                )
            if meeting_result:
                result.append(
                    {
                        "id": forward_to_committee_id,
                        "name": forward_to_committee.get("name", ""),
                        "meetings": meeting_result,
                    }
                )
        return result
