from typing import Any

from ....models.models import Meeting
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import GetMeetingIdFromIdMixin


@register_action("meeting.archive")
class MeetingArchive(UpdateAction, GetMeetingIdFromIdMixin):
    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema()

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)

        messages = []

        active_speaker_exists = self.datastore.exists(
            "speaker",
            And(
                FilterOperator("meeting_id", "=", instance["id"]),
                FilterOperator("begin_time", "!=", None),
                FilterOperator("end_time", "=", None),
            ),
            lock_result=False,
        )
        active_polls = self.datastore.filter(
            "poll",
            And(
                FilterOperator("meeting_id", "=", instance["id"]),
                FilterOperator("state", "=", "started"),
            ),
            ["title"],
            lock_result=False,
        )

        if active_speaker_exists:
            messages.append("speakers")
        if len(active_polls):
            messages.append("polls")
        if len(messages):
            raise ActionException(
                f"Cannot archieve meeting with active {' and '.join(messages)}."
            )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance["is_active_in_organization_id"] = None
        instance["is_archived_in_organization_id"] = 1
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        meeting = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["committee_id"],
            lock_result=False,
        )

        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            meeting["committee_id"],
        ) and not has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            raise PermissionDenied(
                "Missing permissions: Not Committee can_manage and not can_manage_organization"
            )
