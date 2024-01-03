from typing import Any, Dict, List, Set, cast

from ...models import fields
from ...models.base import model_registry
from ...services.datastore.commands import GetManyRequest
from ...shared.exceptions import ActionException
from ..action import Action


class CheckForArchivedMeetingMixin(Action):
    """
    This version of the check_for_archived_meeting-method searches
    for meeting-related fields in the payload and checks, whether
    found meetings are archived or not. Use it for collections
    outside the meeting.
    """

    def check_for_archived_meeting(self, instance: Dict[str, Any]) -> None:
        """check all instance fields for their meeting and if the meeting is active"""
        model = model_registry[self.model.collection]()
        meeting_ids: Set[int] = set()
        if "meeting_id" in instance:
            meeting_ids.add(instance["meeting_id"])
        for fname in instance.keys():
            model_field = model.try_get_field(fname)
            if isinstance(model_field, fields.BaseGenericRelationField):
                raise NotImplementedError()
            if (
                isinstance(model_field, fields.RelationField)
                and tuple(model_field.to.keys())[0] == "meeting"  # type: ignore
            ):
                meeting_ids.add(instance[fname])
            elif (
                isinstance(model_field, fields.RelationListField)
                and tuple(model_field.to.keys())[0] == "meeting"  # type: ignore
            ):
                meeting_ids.update(instance[fname])
        if meeting_ids:
            meetings = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting",
                        cast(List[int], meeting_ids),
                        ["is_active_in_organization_id"],
                    )
                ]
            )["meeting"]
            archived_meetings = [
                str(meeting_id)
                for meeting_id, value in meetings.items()
                if not value.get("is_active_in_organization_id")
            ]

            if archived_meetings and not self.skip_archived_meeting_check:
                raise ActionException(
                    f'Meetings {", ".join(archived_meetings)} cannot be changed, because they are archived.'
                )
