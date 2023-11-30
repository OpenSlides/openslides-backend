import time
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


@register_action("speaker.pause")
class SpeakerPause(SingularActionMixin, CountdownControl, UpdateAction):
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
            or db_instance.get("pause_time") is not None
        ):
            raise ActionException("Speaker is not currently speaking.")

        instance["pause_time"] = round(time.time())

        # update countdowns
        self.control_los_countdown(db_instance["meeting_id"], CountdownCommand.STOP)
        if level_id := db_instance.get("structure_level_list_of_speakers_id"):
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [
                    {
                        "id": level_id,
                        "current_start_time": None,
                        "spoken_time": instance["pause_time"]
                        - db_instance["begin_time"]
                        - db_instance.get("total_pause", 0),
                    }
                ],
            )
        return instance
