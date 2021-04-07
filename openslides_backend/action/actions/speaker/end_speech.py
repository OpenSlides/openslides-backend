import time

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projector_countdown.mixins import CountdownControl


@register_action("speaker.end_speech")
class SpeakerEndSpeach(CountdownControl, UpdateAction):
    """
    Action to stop speakers.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="End speach schema",
        description="Schema to stop a speaker's speach.",
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            speaker = self.datastore.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["begin_time", "end_time", "meeting_id"],
                lock_result=True,
            )
            if speaker.get("begin_time") is None or speaker.get("end_time") is not None:
                raise ActionException(
                    f"Speaker {instance['id']} is not speaking at the moment."
                )
            instance["end_time"] = round(time.time())

            # reset projector_countdown
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), speaker["meeting_id"]),
                [
                    "list_of_speakers_couple_countdown",
                    "list_of_speakers_countdown_id",
                ],
            )
            if meeting.get("list_of_speakers_couple_countdown") and meeting.get(
                "list_of_speakers_countdown_id"
            ):
                self.control_countdown(
                    meeting["list_of_speakers_countdown_id"], "reset"
                )
            yield instance
