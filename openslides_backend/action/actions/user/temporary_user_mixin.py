from typing import Any, Dict

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection
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
            group_ids = instance.pop("group_ids")
            if group_ids:
                get_many_request = GetManyRequest(
                    Collection("group"), group_ids, ["id", "meeting_id"]
                )
                result = self.datastore.get_many([get_many_request])
                groups = result.get(Collection("group"), {}).values()
                for group in groups:
                    if group.get("meeting_id") != instance["meeting_id"]:
                        raise ActionException(
                            f"Group {group['id']} is not in the meeting of the temporary user."
                        )
            instance["group_$_ids"] = {instance["meeting_id"]: group_ids}

        for field in [
            "vote_delegations_$_from_ids",
            "vote_delegated_$_to_id",
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
