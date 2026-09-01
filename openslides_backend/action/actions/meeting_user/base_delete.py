from typing import Any

from openslides_backend.action.actions.poll_option.update import PollOptionUpdate
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import MeetingUser
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema


class MeetingUserBaseDelete(DeleteAction):
    """
    Base action to delete a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_delete_schema()

    def get_history_information(self) -> HistoryInformation | None:
        users = self.get_instances_with_fields(["user_id", "meeting_id"])
        return {
            fqid_from_collection_and_id("user", user["user_id"]): [
                "Participant removed from meeting {}",
                fqid_from_collection_and_id("meeting", user["meeting_id"]),
            ]
            for user in users
        }

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        db_instance = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]),
            ["poll_option_ids", "user_id"],
        )
        if "poll_option_ids" in db_instance:
            remaining_ids = [
                id_
                for id_ in db_instance["poll_option_ids"]
                if not self.datastore.is_to_be_deleted(
                    fqid_from_collection_and_id("poll_option", id_)
                )
            ]
            user_fqid = fqid_from_collection_and_id("user", db_instance["user_id"])
            content_object_id = (
                None if self.datastore.is_to_be_deleted(user_fqid) else user_fqid
            )
            self.execute_other_action(
                PollOptionUpdate,
                [
                    {
                        "id": id_,
                        "content_object_id": content_object_id,
                    }
                    for id_ in remaining_ids
                ],
                skip_archived_meeting_check=True,
            )
        return super().base_update_instance(instance)
