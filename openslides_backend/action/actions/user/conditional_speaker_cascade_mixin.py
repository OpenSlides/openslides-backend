from typing import Any

from openslides_backend.shared.filters import And, FilterOperator

from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ..speaker.delete import SpeakerDeleteAction
from ..user.set_present import UserSetPresentAction


class ConditionalSpeakerCascadeMixinHelper(Action):
    def conditionally_delete_speakers(self, speaker_ids: list[int]) -> None:
        speaker_to_read_ids = [
            speaker_id
            for speaker_id in speaker_ids
            if not self.datastore.is_deleted(
                fqid_from_collection_and_id("speaker", speaker_id)
            )
        ]
        speakers = self.datastore.get_many(
            [
                GetManyRequest(
                    "speaker",
                    speaker_to_read_ids,
                    [
                        "begin_time",
                        "id",
                    ],
                )
            ]
        ).get("speaker", {})
        speakers_to_delete = [
            speaker
            for speaker in speakers.values()
            if speaker.get("begin_time") is None
        ]

        if len(speakers_to_delete):
            self.execute_other_action(
                SpeakerDeleteAction,
                [{"id": speaker["id"]} for speaker in speakers_to_delete],
            )

    def remove_presence(self, user_id: int, meeting_id: int) -> None:
        self.execute_other_action(
            UserSetPresentAction,
            [
                {
                    "id": user_id,
                    "meeting_id": meeting_id,
                    "present": False,
                }
            ],
        )


class ConditionalSpeakerCascadeMixin(ConditionalSpeakerCascadeMixinHelper):
    """
    Mixin for user actions that deletes unstarted speeches of users that were either deleted, or removed from a meeting
    """

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        removed_meeting_id = self.get_removed_meeting_id(instance)
        if removed_meeting_id is not None:
            filter_: Any = FilterOperator("user_id", "=", instance["id"])
            if removed_meeting_id:
                filter_ = And(
                    filter_, FilterOperator("meeting_id", "=", removed_meeting_id)
                )
            meeting_users = self.datastore.filter(
                "meeting_user", filter_, ["speaker_ids"]
            )
            speaker_ids = [
                speaker_id
                for val in meeting_users.values()
                if val.get("speaker_ids")
                for speaker_id in val.get("speaker_ids", [])
            ]
            self.conditionally_delete_speakers(speaker_ids)
            self.remove_presence(instance["id"], removed_meeting_id)

        return super().update_instance(instance)

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        """
        Get the id of the meetings from which the user is removed.
        If the user is removed from all meetings, the return value will be 0.
        If the user is removed from no meetings, it will be None.
        """
        raise NotImplementedError()
