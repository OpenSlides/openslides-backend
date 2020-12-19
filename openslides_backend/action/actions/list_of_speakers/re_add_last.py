from typing import Any, Dict, Iterable

from ....models.models import ListOfSpeakers
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.write_request_element import WriteRequestElement
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..speaker.create_update_delete import SpeakerCreateAction


@register_action("list_of_speakers.re_add_last")
class ListOfSpeakersReAddLastAction(Action):
    """
    Action to re-add the last speaker to the list.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_default_schema(
        required_properties=["id"],
        title="Re-add last speaker",
        description="Adds the last speaker as new speaker.",
    )
    permission_description = "agenda.can_manage_list_of_speakers"

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        list_of_speakers = self.fetch_model(
            FullQualifiedId(self.model.collection, instance["id"]),
            mapped_fields=["id", "speaker_ids"],
        )
        if not list_of_speakers.get("speaker_ids"):
            raise ActionException(f"List of speakers {instance['id']} has no speakers.")
        filter_obj = FilterOperator("end_time", "!=", None)
        last_speakers = sorted(
            self.datastore.filter(
                Collection("speaker"),
                filter_obj,
                mapped_fields=["end_time", "user_id"],
                lock_result=True,
            ).values(),
            key=lambda speaker: speaker["end_time"],
            reverse=True,
        )
        if not last_speakers:
            raise ActionException("There is no last speaker that can be re-added.")
        self.execute_other_action(
            SpeakerCreateAction,
            [
                {
                    "list_of_speakers_id": list_of_speakers["id"],
                    "user_id": last_speakers[0]["user_id"],
                }
            ],
        )
        return instance

    def create_write_request_elements(
        self, instance: Dict[str, Any]
    ) -> Iterable[WriteRequestElement]:
        # we do not create write requests here since everything was delegated to the
        # speaker.create action
        return []
