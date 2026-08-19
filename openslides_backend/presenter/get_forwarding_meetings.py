from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import fastjsonschema

from openslides_backend.shared.filters import And, FilterOperator, Or

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
        request_meeting_id = self.data["meeting_id"]
        if not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_FORWARD,
            request_meeting_id,
        ):
            msg = "You are not allowed to perform presenter get_forwarding_meetings"
            msg += f" Missing permission: {Permissions.Motion.CAN_FORWARD}"
            raise PermissionDenied(msg)

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", request_meeting_id),
            ["committee_id", "is_active_in_organization_id", "name"],
        )
        if not meeting.get("is_active_in_organization_id"):
            raise PresenterException(
                "Your sender meeting is an archived meeting, which can not forward motions."
            )

        committee = self.datastore.get(
            fqid_from_collection_and_id("committee", meeting["committee_id"]),
            ["forward_to_committee_ids"],
        )

        result = []
        for forward_to_committee_id in committee.get("forward_to_committee_ids", []):
            forward_to_committee = self.datastore.get(
                fqid_from_collection_and_id("committee", forward_to_committee_id),
                ["meeting_ids", "name", "default_meeting_id"],
            )
            forward_to_committee_meetings = self.datastore.filter(
                "meeting",
                And(
                    FilterOperator("is_active_in_organization_id", "!=", None),
                    Or(
                        FilterOperator("id", "=", id_)
                        for id_ in forward_to_committee.get("meeting_ids", [])
                        if id_ != request_meeting_id
                    ),
                ),
                ["name", "start_time", "end_time", "time_zone"],
            )

            meetings_list = []
            for meeting_id, meeting_data in forward_to_committee_meetings.items():
                end_time = meeting_data.get("end_time")
                meeting_timezone = meeting_data.get("time_zone") or "UTC"
                start_of_today = datetime.now(tz=ZoneInfo(meeting_timezone)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                if end_time is None or end_time >= start_of_today:
                    meetings_list.append(
                        {
                            "id": meeting_id,
                            "name": meeting_data.get("name", ""),
                            "start_time": self._get_formatted_datetime_value(
                                meeting_data.get("start_time"), meeting_timezone
                            ),
                            "end_time": self._get_formatted_datetime_value(
                                end_time, meeting_timezone
                            ),
                        }
                    )
            if meetings_list:
                result.append(
                    {
                        "id": forward_to_committee_id,
                        "name": forward_to_committee.get("name", ""),
                        "meetings": meetings_list,
                        "default_meeting_id": forward_to_committee.get(
                            "default_meeting_id"
                        ),
                    }
                )
        return result

    @staticmethod
    def _get_formatted_datetime_value(value: Any, timezone: str) -> str | None:
        if not value:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value_with_timezone = value.replace(tzinfo=ZoneInfo(timezone))
            else:
                value_with_timezone = value.astimezone(ZoneInfo(timezone))
            return value_with_timezone.isoformat()
        return str(value)
