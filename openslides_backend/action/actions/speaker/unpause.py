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


@register_action("speaker.unpause")
class SpeakerUnpause(SingularActionMixin, CountdownControl, UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "begin_time",
                "end_time",
                "pause_time",
                "total_pause",
                "meeting_id",
                "structure_level_list_of_speakers_id",
            ],
        )
        if (
            db_instance.get("begin_time") is None
            or db_instance.get("end_time") is not None
            or db_instance.get("pause_time") is None
        ):
            raise ActionException("Speaker is not paused.")

        instance["unpause_time"] = now = round(time())
        instance["total_pause"] = (
            db_instance.get("total_pause", 0) + now - db_instance["pause_time"]
        )
        instance["pause_time"] = None

        # update countdowns
        self.control_los_countdown(db_instance["meeting_id"], CountdownCommand.START)
        if level_id := db_instance.get("structure_level_list_of_speakers_id"):
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [
                    {
                        "id": level_id,
                        "current_start_time": now,
                    }
                ],
            )
        return instance
