from time import time
from typing import Any

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


@register_action("speaker.unpause")
class SpeakerUnpause(SingularActionMixin, CountdownControl, UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "begin_time",
                "end_time",
                "pause_time",
                "total_pause",
                "speech_state",
                "meeting_id",
                "list_of_speakers_id",
                "structure_level_list_of_speakers_id",
            ],
        )
        if (
            db_instance.get("begin_time") is None
            or db_instance.get("end_time") is not None
            or db_instance.get("pause_time") is None
        ):
            raise ActionException("Speaker is not paused.")

        # find current speaker, if exists, and pause it
        result = self.datastore.filter(
            self.model.collection,
            And(
                FilterOperator("meeting_id", "=", db_instance["meeting_id"]),
                FilterOperator(
                    "list_of_speakers_id", "=", db_instance["list_of_speakers_id"]
                ),
                FilterOperator("begin_time", "!=", None),
                FilterOperator("pause_time", "=", None),
                FilterOperator("end_time", "=", None),
            ),
            mapped_fields=["id"],
        )
        if result:
            self.execute_other_action(SpeakerPause, [{"id": next(iter(result.keys()))}])

        instance["unpause_time"] = now = round(time())
        instance["total_pause"] = (
            db_instance.get("total_pause", 0) + now - db_instance["pause_time"]
        )
        instance["pause_time"] = None

        # update countdowns
        self.control_los_countdown(db_instance["meeting_id"], CountdownCommand.START)
        self.start_structure_level_countdown(now, db_instance)
        return instance
