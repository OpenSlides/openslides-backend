from ...action import Action
from ...util.typing import ActionData

class ConditionalSpeakerCascadeMixin(Action):
    """
    Mixin for user actions that deletes unstarted speeches of users that were either deleted, or removed from a meeting
    """

    def prefetch(self, action_data: ActionData) -> None:
        users = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    list(
                        {
                            instance["id"]
                            for instance in action_data
                        }
                    ),
                    [
                        "meeting_user_ids",
                    ],
                )
            ]
        )
        meeting_users = self.datastore.get_many(
            [
                "meeting_user",
                list(
                    {
                        meeting_user_id
                        for instance in users
                        for meeting_user_id in instance.get("meeting_user_ids", [])
                    }
                ),
                [
                    "speaker_ids",
                ]
            ]
        )
        bonjour = self.datastore.get_many(
            [
                "speaker",
                list(
                    {
                        speaker_id
                        for instance in meeting_users
                        for speaker_id in instance.get("speaker_ids", [])
                    }
                ),
                [
                    "begin_time",
                ]
            ]
        )
        return bonjour


    # def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
    #     if instance["id"] == self.user_id:
    #         raise ActionException("You cannot delete yourself.")
    #     return instance