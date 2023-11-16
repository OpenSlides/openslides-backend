import time
from typing import Any, Dict

from openslides_backend.action.actions.speaker.end_speech import SpeakerEndSpeach
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
from ..projector_countdown.mixins import CountdownControl


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
            mapped_fields=[
                "list_of_speakers_id",
                "meeting_id",
                "begin_time",
                "end_time",
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
            mapped_fields=["id"],
        )
        if result:
            self.execute_other_action(
                SpeakerEndSpeach, [{"id": next(iter(result.keys()))}]
            )

        now = round(time.time())
        if db_instance.get("begin_time") is not None:
            raise ActionException("Speaker has already started to speak.")
        assert db_instance.get("end_time") is None
        instance["begin_time"] = now

        # reset projector countdown
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", db_instance["meeting_id"]),
            [
                "list_of_speakers_couple_countdown",
                "list_of_speakers_countdown_id",
            ],
            lock_result=False,
        )
        if meeting.get("list_of_speakers_couple_countdown") and meeting.get(
            "list_of_speakers_countdown_id"
        ):
            self.control_countdown(meeting["list_of_speakers_countdown_id"], "restart")

        # update structure level countdown
        if level_id := db_instance.get("structure_level_list_of_speakers_id"):
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [{"id": level_id, "current_start_time": now}],
            )

        return instance
