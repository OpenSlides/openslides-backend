from time import time
from typing import Any

from openslides_backend.action.util.typing import ActionData

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.mixins import CountdownCommand, CountdownControl
from ..user.delegation_based_restriction_mixin import DelegationBasedRestrictionMixin


@register_action("speaker.delete")
class SpeakerDeleteAction(
    DeleteAction, CountdownControl, DelegationBasedRestrictionMixin
):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def check_permissions(self, instance: dict[str, Any]) -> None:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id"],
            lock_result=False,
        )
        if speaker.get("meeting_user_id"):
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", speaker["meeting_user_id"]),
                ["user_id"],
            )

            restricted = self.check_delegator_restriction(
                "users_forbid_delegator_in_list_of_speakers",
                [self.get_meeting_id(instance)],
            )
            if meeting_user.get("user_id") == self.user_id and not len(restricted):
                return
        super().check_permissions(instance)

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.end_time = round(time())
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        speaker = self.datastore.get(
            fqid_from_collection_and_id("speaker", instance["id"]),
            [
                "meeting_id",
                "begin_time",
                "end_time",
                "pause_time",
                "speech_state",
                "point_of_order",
                "unpause_time",
                "structure_level_list_of_speakers_id",
            ],
        )
        if (
            speaker.get("begin_time")
            and not speaker.get("end_time")
            and not speaker.get("pause_time")
        ):
            self.decrease_structure_level_countdown(self.end_time, speaker)
        self.control_los_countdown(speaker["meeting_id"], CountdownCommand.RESET)
        return super().update_instance(instance)
