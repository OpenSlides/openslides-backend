from time import time
from typing import Any, Dict

from openslides_backend.action.actions.structure_level_list_of_speakers.update import (
    StructureLevelListOfSpeakersUpdateAction,
)
from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin

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
                "meeting_id",
                "structure_level_list_of_speakers_id",
            ],
        )
        if speaker.get("begin_time") is None or speaker.get("end_time") is not None:
            raise ActionException(
                f"Speaker {instance['id']} is not speaking at the moment."
            )
        instance["end_time"] = now = round(time())

        if speaker.get("pause_time"):
            instance["total_pause"] = (
                speaker.get("total_pause", 0)
                + instance["end_time"]
                - speaker["pause_time"]
            )
            instance["pause_time"] = None
        elif level_id := speaker.get("structure_level_list_of_speakers_id"):
            # only update the level if the speaker was not paused
            start_time = speaker.get("unpause_time", speaker["begin_time"])
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [
                    {
                        "id": level_id,
                        "current_start_time": None,
                        "spoken_time": now - start_time,
                    }
                ],
            )

        self.control_los_countdown(speaker["meeting_id"], CountdownCommand.RESET)
        return instance
