from typing import Any, Dict

from ....models.models import User
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ...action import Action


class TemporaryUserMixin(Action):
    def update_instance_temporary_user(
        self, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        present_in_meeting_ids = instance.get("is_present_in_meeting_ids")
        if present_in_meeting_ids and any(
            id != instance["meeting_id"] for id in present_in_meeting_ids
        ):
            raise ActionException(
                "A temporary user can only be present in its respective meeting."
            )

        if "group_ids" in instance:
            self.check_equal_fields(
                User.group__ids, instance, "group_ids", ["meeting_id"]
            )
            group_ids = instance.pop("group_ids")
            instance["group_$_ids"] = {instance["meeting_id"]: group_ids}

        if "vote_delegations_from_ids" in instance:
            vote_delegations_from_ids = instance.pop("vote_delegations_from_ids")
            get_many_request = GetManyRequest(
                self.model.collection, vote_delegations_from_ids, ["id"]
            )
            gm_result = self.datastore.get_many([get_many_request])
            users = gm_result.get(self.model.collection, {})

            set_action_data = set(vote_delegations_from_ids)
            diff = set_action_data.difference(users.keys())
            if len(diff):
                raise ActionException(f"The following users were not found: {diff}")

            instance["vote_delegations_$_from_ids"] = {
                instance["meeting_id"]: vote_delegations_from_ids
            }

        for field in [
            "comment_$",
            "number_$",
            "structure_level_$",
            "about_me_$",
            "vote_weight_$",
        ]:
            instance_field = field.replace("_$", "")
            if instance_field in instance:
                instance[field] = {instance["meeting_id"]: instance.pop(instance_field)}

        return instance
