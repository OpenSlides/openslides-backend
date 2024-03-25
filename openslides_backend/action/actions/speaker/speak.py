import time
from typing import Any

from openslides_backend.action.action import Action
from openslides_backend.action.actions.speaker.end_speech import SpeakerEndSpeach
from openslides_backend.action.actions.speaker.pause import SpeakerPause
from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin
from openslides_backend.shared.filters import And, FilterOperator

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.mixins import CountdownCommand, CountdownControl
from .speech_state import SpeechState


@register_action("speaker.speak")
class SpeakerSpeak(SingularActionMixin, CountdownControl, UpdateAction):
    """
    Action to let speakers speak.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="Speak schema",
        description="Schema to let a speaker's speach begin.",
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "list_of_speakers_id",
                "meeting_id",
                "begin_time",
                "end_time",
                "speech_state",
                "structure_level_list_of_speakers_id",
                "point_of_order",
            ],
        )
        # find current speaker(s), if they exists, and end their speech
        result = self.datastore.filter(
            self.model.collection,
            And(
                FilterOperator("meeting_id", "=", db_instance["meeting_id"]),
                FilterOperator(
                    "list_of_speakers_id", "=", db_instance["list_of_speakers_id"]
                ),
                FilterOperator("begin_time", "!=", None),
                FilterOperator("end_time", "=", None),
            ),
            mapped_fields=["id", "pause_time"],
        )
        action: type[Action]
        if db_instance.get("speech_state") == SpeechState.INTERPOSED_QUESTION:
            # pause currently speaking speaker
            action = SpeakerPause
            action_data = [
                {"id": speaker["id"]}
                for speaker in result.values()
                if speaker.get("pause_time") is None
            ]
        else:
            # stop all paused or speaking speakers
            action = SpeakerEndSpeach
            action_data = [{"id": speaker["id"]} for speaker in result.values()]
        if action_data:
            self.execute_other_action(action, action_data)

        now = round(time.time())
        if db_instance.get("begin_time") is not None:
            raise ActionException("Speaker has already started to speak.")
        assert db_instance.get("end_time") is None
        instance["begin_time"] = now

        # update countdowns, differentiate by speaker type
        countdown_time: int | None = None
        if db_instance.get("speech_state") == SpeechState.INTERVENTION:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", db_instance["meeting_id"]),
                ["list_of_speakers_intervention_time"],
            )
            countdown_time = meeting["list_of_speakers_intervention_time"]
        elif db_instance.get("speech_state") == SpeechState.INTERPOSED_QUESTION:
            countdown_time = 0
        self.control_los_countdown(
            db_instance["meeting_id"], CountdownCommand.RESTART, countdown_time
        )
        self.start_structure_level_countdown(now, db_instance)
        return instance
