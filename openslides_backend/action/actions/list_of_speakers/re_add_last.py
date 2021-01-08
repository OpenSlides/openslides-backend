from typing import Any, Dict

from ....models.models import ListOfSpeakers, Speaker
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("list_of_speakers.re_add_last")
class ListOfSpeakersReAddLastAction(UpdateAction):
    """
    Action to re-add the last speaker to the list.
    """

    model = Speaker()
    schema = DefaultSchema(ListOfSpeakers()).get_default_schema(
        required_properties=["id"],
        title="Re-add last speaker",
        description="Moves the last speaker back to the top of the list.",
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Check if list of speakers has speakers.
        list_of_speakers_id = instance["id"]
        list_of_speakers = self.fetch_model(
            FullQualifiedId(ListOfSpeakers().collection, list_of_speakers_id),
            mapped_fields=["speaker_ids"],
        )
        if not list_of_speakers.get("speaker_ids"):
            raise ActionException(
                f"List of speakers {list_of_speakers_id} has no speakers."
            )

        # Fetch last speaker.
        last_speakers = sorted(
            self.datastore.filter(
                self.model.collection,
                FilterOperator("end_time", "!=", None),
                mapped_fields=["end_time", "user_id"],
                lock_result=True,
            ).items(),
            key=lambda item: item[1]["end_time"],
            reverse=True,
        )
        if not last_speakers:
            raise ActionException("There is no last speaker that can be re-added.")
        last_speaker = last_speakers[0][1]
        last_speaker.update({"id": last_speakers[0][0]})

        # Check if this last speaker is already on the list of coming speakers.
        if self.datastore.exists(
            self.model.collection,
            And(
                FilterOperator("begin_time", "=", None),
                FilterOperator("user_id", "=", last_speaker["user_id"]),
            ),
        )["exists"]:
            raise ActionException(
                f"User {last_speaker['user_id']} is already on the list of speakers."
            )

        # Fetch all speakers and sort them.
        all_speakers = sorted(
            self.datastore.filter(
                self.model.collection,
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                mapped_fields=["weight", "user_id"],
                lock_result=True,
            ).values(),
            key=lambda speaker: speaker.get("weight") or 0,
        )
        weight = all_speakers[0]["weight"] or 0

        # Return new instance to the generic part of the UpdateAction.
        return {
            "id": last_speaker["id"],
            "begin_time": None,
            "end_time": None,
            "weight": weight - 1,
        }
