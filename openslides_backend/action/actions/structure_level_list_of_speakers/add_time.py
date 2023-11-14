from openslides_backend.action.actions.structure_level_list_of_speakers.create import (
    StructureLevelListOfSpeakersCreateAction,
)
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin
from openslides_backend.action.util.typing import ActionData
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import StructureLevelListOfSpeakers
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level_list_of_speakers.add_time")
class StructureLevelListOfSpeakersAddTimeAction(SingularActionMixin, UpdateAction):
    model = StructureLevelListOfSpeakers()
    schema = DefaultSchema(StructureLevelListOfSpeakers()).get_update_schema()
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        instance = next(iter(action_data))
        meeting_id = self.get_meeting_id(instance)
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    self.model.collection,
                    [instance["id"]],
                    ["current_start_time", "remaining_time", "list_of_speakers_id"],
                ),
                GetManyRequest("meeting", [meeting_id], ["structure_level_ids"]),
            ]
        )
        db_instance = result[self.model.collection][instance["id"]]
        meeting = result["meeting"][meeting_id]
        if db_instance.get("current_start_time") is not None:
            raise ActionException("Stop the current speaker before adding time")
        if db_instance["remaining_time"] >= 0:
            raise ActionException(
                "You can only add time if the remaining time is negative"
            )

        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "structure_level",
                    meeting["structure_level_ids"],
                    ["allow_additional_time"],
                ),
                GetManyRequest(
                    "list_of_speakers",
                    [db_instance["list_of_speakers_id"]],
                    ["structure_level_list_of_speakers_ids"],
                ),
            ]
        )
        structure_levels = result["structure_level"]
        los = result["list_of_speakers"][db_instance["list_of_speakers_id"]]
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    self.model.collection,
                    los["structure_level_list_of_speakers_ids"],
                    ["id", "structure_level_id", "additional_time", "remaining_time"],
                ),
            ]
        )
        sllos_map = {
            sllos["structure_level_id"]: sllos
            for sllos in result[self.model.collection].values()
        }
        for id, structure_level in structure_levels.items():
            if structure_level.get("allow_additional_time"):
                if not (sllos := sllos_map.get(id)):
                    action_results = self.execute_other_action(
                        StructureLevelListOfSpeakersCreateAction,
                        [
                            {
                                "structure_level_id": id,
                                "list_of_speakers_id": db_instance[
                                    "list_of_speakers_id"
                                ],
                            }
                        ],
                    )
                    assert action_results and action_results[0]
                    sllos = self.datastore.get(
                        fqid_from_collection_and_id(
                            self.model.collection, action_results[0]["id"]
                        ),
                        ["id", "additional_time", "remaining_time"],
                    )
                t = db_instance["remaining_time"]
                yield {
                    "id": sllos["id"],
                    "additional_time": sllos.get("additional_time", 0) - t,
                    "remaining_time": sllos["remaining_time"] - t,
                }
