from typing import Any, Dict, List

from ...shared.filters import And, FilterOperator
from ..action import Action


class GroupHelper(Action):
    def get_groups_from_meeting_user(self, meeting_id: int, user_id: int) -> List[int]:
        meeting_user = self.get_meeting_user(meeting_id, user_id)
        if not meeting_user:
            return []
        return meeting_user.get("group_ids") or []

    def get_meeting_user(self, meeting_id: int, user_id: int) -> Dict[str, Any]:
        filtered_results = self.datastore.filter(
            "meeting_user",
            And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("user_id", "=", user_id),
            ),
            ["id", "group_ids"],
        )
        if not filtered_results:
            return {}
        return list(filtered_results.values())[0]
