import time
from typing import Any, Dict, Optional, Type

from openslides_backend.action.action import Action
from openslides_backend.action.actions.speaker.end_speech import SpeakerEndSpeach
from openslides_backend.action.actions.speaker.pause import SpeakerPause
from openslides_backend.action.actions.structure_level_list_of_speakers.update import (
    StructureLevelListOfSpeakersUpdateAction,
)
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
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
            ],
        )
        # find current speaker, if exists, and end their speech
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
        if result:
            current_speaker = next(iter(result.values()))
            action: Optional[Type[Action]] = None
            if db_instance.get("speech_state") == SpeechState.INTERPOSED_QUESTION:
                if current_speaker.get("pause_time") is None:
                    action = SpeakerPause
            else:
                action = SpeakerEndSpeach
            if action:
                self.execute_other_action(action, [{"id": current_speaker["id"]}])

        now = round(time.time())
        if db_instance.get("begin_time") is not None:
            raise ActionException("Speaker has already started to speak.")
        assert db_instance.get("end_time") is None
        instance["begin_time"] = now

        # update countdowns, differentiate by speaker type
        countdown_time: Optional[int] = None
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
        if db_instance.get("speech_state") not in (
            SpeechState.INTERPOSED_QUESTION,
            SpeechState.INTERVENTION,
        ) and (level_id := db_instance.get("structure_level_list_of_speakers_id")):
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [{"id": level_id, "current_start_time": now}],
            )

        return instance
