from typing import Any, Dict

from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action

ONE_ORGANIZATION_ID = 1


class ChatEnabledMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_id = self.get_meeting_id(instance)
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["enable_chat"],
        )
        organization = self.datastore.get(
            FullQualifiedId(Collection("organization"), ONE_ORGANIZATION_ID),
            ["enable_chat"],
        )

        if not meeting.get("enable_chat") or not organization.get("enable_chat"):
            raise ActionException("Chat is not enabled.")
        return instance


class CheckUniqueNameMixin(Action):
    def check_name_unique(self, instance: Dict[str, Any]) -> None:
        meeting_id = self.get_meeting_id(instance)
        name_exists = self.datastore.exists(
            self.model.collection,
            And(
                FilterOperator("name", "=", instance["name"]),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
        )
        if name_exists:
            raise ActionException("The name of a chat group must be unique.")
