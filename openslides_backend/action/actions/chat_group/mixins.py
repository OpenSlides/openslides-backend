from typing import Any, Dict

from ....models.models import Model
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action

ONE_ORGANIZATION_ID = 1


class MeetingIdProvider:
    datastore: DatastoreService
    model: Model

    def fetch_meeting_id(self, instance: Dict[str, Any]) -> int:
        meeting_id = instance.get("meeting_id")
        if not meeting_id:
            chat_group = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
            )
            meeting_id = chat_group["meeting_id"]
        return meeting_id


class ChatEnabledMixin(MeetingIdProvider, Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_id = self.fetch_meeting_id(instance)
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


class CheckUniqueNameMixin(MeetingIdProvider, Action):
    def check_name_unique(self, instance: Dict[str, Any]) -> None:
        meeting_id = self.fetch_meeting_id(instance)
        name_exists = self.datastore.exists(
            self.model.collection,
            And(
                FilterOperator("name", "=", instance["name"]),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
        )
        if name_exists:
            raise ActionException("The name of a chat group must be unique.")
