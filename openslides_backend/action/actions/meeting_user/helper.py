from ....action.action import Action
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from .create import MeetingUserCreate


class MeetingUserHelper(Action):
    def create_or_get_meeting_user(self, meeting_id: int, user_id: int) -> int:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("user_id", "=", user_id),
        )
        result = self.datastore.filter("meeting_user", filter_, ["id"])
        if result:
            return int(list(result)[0])
        else:
            action_results = self.execute_other_action(
                MeetingUserCreate,
                [{"meeting_id": meeting_id, "user_id": user_id}],
            )
            id_ = action_results[0]["id"]  # type: ignore
            self.datastore.changed_models.get(fqid_from_collection_and_id("meeting_user", id_), {}).pop("meta_new", None)
            return id_
