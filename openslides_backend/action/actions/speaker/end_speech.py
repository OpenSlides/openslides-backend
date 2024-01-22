from time import time
from typing import Any, Dict

from openslides_backend.action.actions.speaker.delete import SpeakerDeleteAction
from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin
from openslides_backend.action.util.typing import ActionData
from openslides_backend.shared.filters import And, FilterOperator

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.mixins import CountdownCommand, CountdownControl


@register_action("speaker.end_speech")
class SpeakerEndSpeach(SingularActionMixin, CountdownControl, UpdateAction):
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
        self.end_time = round(time())
        instance = next(iter(action_data))
        yield instance
        # additionally yield all child interposed questions
        db_instance = self.datastore.get(
            fqid_from_collection_and_id("speaker", instance["id"]),
            ["list_of_speakers_id", "meeting_id", "speech_state"],
        )
        if db_instance.get("speech_state") != SpeechState.INTERPOSED_QUESTION:
            result = self.datastore.filter(
                "speaker",
                And(
                    FilterOperator("meeting_id", "=", db_instance["meeting_id"]),
                    FilterOperator(
                        "list_of_speakers_id", "=", db_instance["list_of_speakers_id"]
                    ),
                    FilterOperator(
                        "speech_state", "=", SpeechState.INTERPOSED_QUESTION
                    ),
                    FilterOperator("end_time", "=", None),
                ),
                ["begin_time"],
            )
            for id, speaker in result.items():
                if speaker.get("begin_time") is not None:
                    yield {"id": id}
                else:
                    self.execute_other_action(SpeakerDeleteAction, [{"id": id}])

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "begin_time",
                "end_time",
                "pause_time",
                "unpause_time",
                "total_pause",
                "speech_state",
                "meeting_id",
                "structure_level_list_of_speakers_id",
            ],
        )
        if speaker.get("begin_time") is None or speaker.get("end_time") is not None:
            raise ActionException(
                f"Speaker {instance['id']} is not speaking at the moment."
            )
        instance["end_time"] = self.end_time

        if speaker.get("pause_time"):
            instance["total_pause"] = (
                speaker.get("total_pause", 0)
                + instance["end_time"]
                - speaker["pause_time"]
            )
            instance["pause_time"] = None
        else:
            self.decrease_structure_level_countdown(self.end_time, speaker)

        self.control_los_countdown(speaker["meeting_id"], CountdownCommand.RESET)
        return instance
