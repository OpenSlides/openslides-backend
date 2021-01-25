from typing import Any, Dict

from ....models.models import Speaker
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
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
        optional_properties=["marked", "point_of_order"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("point_of_order", False):
            result = self.datastore.min(
                collection=Collection("speaker"),
                filter=FilterOperator(
                    "list_of_speakers_id", "=", instance["list_of_speakers_id"]
                ),
                field="weight",
                type="int",
                lock_result=True,
            )
            instance["weight"] = -1 if result["min"] is None else result["min"] - 1
        return instance

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks
        - that a new speaker does not already exist on the list of speaker as
        comming speaker (with begin_time == None), but allows one additional with point_of_order speaker per user
        - checks, if points_of_order are used inthis meeting
        - checks, if user has to be present to be added to the list of speakers

        """
        
        los_fqid = FullQualifiedId(
            Collection("list_of_speakers"), instance["list_of_speakers_id"]
        )
        los = self.datastore.get(los_fqid, ["meeting_id"])
        meeting_id = los["meeting_id"]
        meeting_fqid = FullQualifiedId(Collection("meeting"), meeting_id)
        meeting = self.datastore.get(
            meeting_fqid,
            [
                "list_of_speakers_enable_point_of_order_speakers",
                "list_of_speakers_present_users_only",
            ],
        )
        if instance.get("point_of_order") and not meeting.get("list_of_speakers_enable_point_of_order_speakers"):
            raise ActionException(
                "Point of order speakers are not enabled for this meeting."
            )
        if meeting.get("list_of_speakers_present_users_only"):
            user_fqid = FullQualifiedId(Collection("user"), instance["user_id"])
            user = self.datastore.get(user_fqid, ["is_present_in_meeting_ids"])
            if meeting_id not in user.get("is_present_in_meeting_ids", ()):
                raise ActionException(
                    "Only present users can be on the lists of speakers."
                )

        # Results are necessary, because of getting a lock_result
        filter_obj = And(
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("begin_time", "=", None),
        )
        speakers = self.datastore.filter(
            collection=Collection("speaker"),
            filter=filter_obj,
            mapped_fields=["user_id", "point_of_order"],
            lock_result=True,
        )
        for speaker in speakers.values():
            if speaker["user_id"] == instance["user_id"] and speaker.get(
                "point_of_order"
            ) == instance.get("point_of_order"):
                raise ActionException(
                    f"User {instance['user_id']} is already on the list of speakers."
                )
        return super().validate_fields(instance)


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["marked"])


@register_action("speaker.delete")
class SpeakerDeleteAction(DeleteAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
