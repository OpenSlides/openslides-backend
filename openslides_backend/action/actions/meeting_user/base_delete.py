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
