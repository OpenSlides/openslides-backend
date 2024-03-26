from typing import Any

from openslides_backend.action.actions.speaker.speech_state import SpeechState

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

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # Fetch all speakers.
        list_of_speakers_id = instance["id"]
        meeting_id = self.get_meeting_id(instance)
        speakers = self.datastore.filter(
            self.model.collection,
            And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            mapped_fields=[
                "id",
                "end_time",
                "begin_time",
                "meeting_user_id",
                "weight",
                "point_of_order",
                "speech_state",
            ],
        )
        if not speakers:
            raise ActionException(
                f"List of speakers {list_of_speakers_id} has no speakers."
            )

        # Get last speaker.
        last_speaker, lowest_weight = None, None
        has_current_speaker = False
        for speaker in speakers.values():
            speaker_weight = speaker.get("weight") or 0
            if lowest_weight is None or speaker_weight < lowest_weight:
                lowest_weight = speaker_weight

            if speaker.get("end_time") is not None:
                if last_speaker is None or self.get_order(speaker) < self.get_order(
                    last_speaker
                ):
                    last_speaker = speaker
            elif speaker.get("begin_time") is not None:
                has_current_speaker = True
        if last_speaker is None:
            raise ActionException("There is no last speaker that can be re-added.")
        assert isinstance(lowest_weight, int)
        if (
            last_speaker.get("speech_state") == "interposed_question"
            and not has_current_speaker
        ):
            raise ActionException(
                "Can't re-add interposed question when there's no current speaker"
            )

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["list_of_speakers_allow_multiple_speakers"],
        )
        if not meeting.get("list_of_speakers_allow_multiple_speakers"):
            for speaker in speakers.values():
                if (
                    speaker.get("end_time") is None
                    and last_speaker.get("meeting_user_id")
                    and speaker.get("meeting_user_id")
                    == last_speaker.get("meeting_user_id")
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
            "id": last_speaker["id"],
            "begin_time": None,
            "end_time": None,
            "weight": lowest_weight - 1,
        }

    def get_order(self, instance: dict[str, Any]) -> tuple[int, bool, int]:
        """
        Defines which speaker should be re-added first:
        1. The speaker with the latest end_time.
        2. If the speaker is an interposed question, it should be re-added after the parent item.
        3. Between multiple interposed questions, the weight decides.
        """
        return (
            -instance["end_time"],
            instance["speech_state"] == SpeechState.INTERPOSED_QUESTION,
            instance["weight"],
        )
