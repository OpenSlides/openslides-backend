from typing import Any, Dict

from ....models.models import Speaker
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.delete import DeleteAction
from ...generics.update import UpdateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("speaker.create")
class SpeakerCreateAction(CreateActionWithInferredMeeting):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "user_id"],
        optional_properties=["marked"],
    )
    permission_description = PERMISSION_SPECIAL_CASE

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks that a new speaker does not already exist on the list of speaker as
        comming speaker (with begin_time == None)
        """
        filter_obj = And(
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("begin_time", "=", None),
        )
        speakers = self.datastore.filter(
            collection=Collection("speaker"),
            filter=filter_obj,
            mapped_fields=["user_id"],
            lock_result=True,
        )
        for speaker in speakers.values():
            if speaker["user_id"] == instance["user_id"]:
                raise ActionException(
                    f"User {instance['user_id']} is already on the list of speakers."
                )
        return super().validate_fields(instance)


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["marked"])
    permission_description = "agenda.can_manage_list_of_speakers"


@register_action("speaker.delete")
class SpeakerDeleteAction(DeleteAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
    permission_description = PERMISSION_SPECIAL_CASE
