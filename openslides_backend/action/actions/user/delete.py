from typing import Any, Dict, Optional

from openslides_backend.shared.typing import HistoryInformation

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.delete")
class UserDelete(UserScopeMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance["id"] == self.user_id:
            raise ActionException("You cannot delete yourself.")
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])

    def get_history_information(self) -> Optional[HistoryInformation]:
        return None
        # information = {}
        # users = self.get_instances_with_fields(["id", "group_$_ids"])
        # for user in users:
        #     meeting_ids = user.get("group_$_ids", [])
        #     instance_information = ["Participant deleted"]
        #     if len(meeting_ids) == 1:
        #         instance_information[0] += " in meeting {}"
        #         instance_information.append(
        #             fqid_from_collection_and_id("meeting", meeting_ids.pop())
        #         )
        #     information[
        #         fqid_from_collection_and_id(self.model.collection, user["id"])
        #     ] = instance_information
        # return information
