from openslides_backend.shared.history_events import build_history_information_data
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import MeetingUser
from ....services.database.commands import GetManyRequest
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema


class MeetingUserBaseDelete(DeleteAction):
    """
    Base action to delete a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_delete_schema()

    def get_history_information(self) -> HistoryInformation | None:
        information: HistoryInformation = {}
        meeting_users = self.get_instances_with_fields(["user_id", "meeting_id"])
        users = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    [mu["user_id"] for mu in meeting_users],
                    ["is_present_in_meeting_ids"],
                )
            ],
            lock_result=False,
            use_changed_models=False,
        )["user"]

        for meeting_user in meeting_users:
            information[
                fqid_from_collection_and_id("user", meeting_user["user_id"])
            ] = build_history_information_data(
                [
                    "Participant removed from meeting {}",
                    fqid_from_collection_and_id("meeting", meeting_user["meeting_id"]),
                ],
            )
            if meeting_user["meeting_id"] in users.get(meeting_user["user_id"], {}).get(
                "is_present_in_meeting_ids", []
            ):
                information[
                    fqid_from_collection_and_id("meeting_user", meeting_user["id"])
                ] = build_history_information_data(changed_fields={"is_present": False})
        return information
