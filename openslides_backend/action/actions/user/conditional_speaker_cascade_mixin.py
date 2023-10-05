from typing import Any, Dict, List

from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ..speaker.delete import SpeakerDeleteAction


class ConditionalSpeakerCascadeMixin(Action):
    """
    Mixin for user actions that deletes unstarted speeches of users that were either deleted, or removed from a meeting
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        removed_meeting_ids = self.get_meetings_removed(instance)
        if len(removed_meeting_ids) != 0:
            delete_all = 0 in removed_meeting_ids
            user = self.datastore.get(
                fqid_from_collection_and_id("user", instance["id"]),
                [
                    "meeting_user_ids",
                ],
            )
            meeting_users = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_user",
                        user.get("meeting_user_ids", []),
                        [
                            "speaker_ids",
                            "user_id",
                            "meeting_id",
                        ],
                    )
                ]
            )
            filtered_meeting_users = [
                meeting_user
                for meeting_user in meeting_users.get("meeting_user", {}).values()
                if delete_all or meeting_user["meeting_id"] in removed_meeting_ids
            ]
            speakers = self.datastore.get_many(
                [
                    GetManyRequest(
                        "speaker",
                        [
                            speaker_id
                            for instance in filtered_meeting_users
                            for speaker_id in instance.get("speaker_ids", [])
                        ],
                        [
                            "begin_time",
                            "id",
                        ],
                    )
                ]
            )
            speakers_to_delete = [
                speaker
                for speaker in speakers.get("speaker", {}).values()
                if speaker.get("begin_time") is None
            ]

            if len(speakers_to_delete):
                self.execute_other_action(
                    SpeakerDeleteAction,
                    [{"id": speaker["id"]} for speaker in speakers_to_delete],
                )

        return super().update_instance(instance)

    def get_meetings_removed(self, action_date: Dict[str, Any]) -> List[int]:
        """
        Get the ids of all meetings from which the user is removed. If the user is removed from all meetings, the return value will be [0]
        """
        raise NotImplementedError()
