from typing import Any, Dict

from ....models.models import ListOfSpeakers, Speaker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
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
    permission = Permissions.ListOfSpeakers.CAN_MANAGE
    permission_model = ListOfSpeakers()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Fetch all speakers.
        list_of_speakers_id = instance["id"]
        meeting_id = self.get_meeting_id(instance)
        speakers = self.datastore.filter(
            self.model.collection,
            And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            mapped_fields=["end_time", "meeting_user_id", "weight", "point_of_order"],
        )
        if not speakers:
            raise ActionException(
                f"List of speakers {list_of_speakers_id} has no speakers."
            )

        # Get last speaker.
        last_speaker_id, last_speaker = None, None
        lowest_weight = None
        for speaker_id, speaker in speakers.items():
            speaker_weight = speaker.get("weight") or 0
            if lowest_weight is None:
                lowest_weight = speaker_weight
            else:
                lowest_weight = min(lowest_weight, speaker_weight)

            if speaker.get("end_time") is not None:
                if last_speaker_id is None:
                    last_speaker_id, last_speaker = speaker_id, speaker
                else:
                    if last_speaker["end_time"] < speaker["end_time"]:
                        last_speaker_id, last_speaker = speaker_id, speaker
        if last_speaker is None:
            raise ActionException("There is no last speaker that can be re-added.")
        assert isinstance(lowest_weight, int)

        for speaker in speakers.values():
            if (
                speaker.get("end_time") is None
                and speaker["meeting_user_id"] == last_speaker["meeting_user_id"]
                and bool(speaker.get("point_of_order"))
                == bool(last_speaker.get("point_of_order"))
            ):
                meeting_user = self.datastore.get(
                    fqid_from_collection_and_id(
                        "meeting_user", last_speaker["meeting_user_id"]
                    ),
                    ["user_id"],
                )
                raise ActionException(
                    f"User {meeting_user['user_id']} is already on the list of speakers."
                )

        # Return new instance to the generic part of the UpdateAction.
        return {
            "id": last_speaker_id,
            "begin_time": None,
            "end_time": None,
            "weight": lowest_weight - 1,
        }
