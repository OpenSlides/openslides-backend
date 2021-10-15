from typing import Any, Dict

from ....models.models import User
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import UserMixin


@register_action("user.update")
class UserUpdate(
    UserMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "can_change_own_password",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organization_management_level",
            "committee_ids",
            "committee_$_management_level",
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "group_$_ids",
            "is_demo_user",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if (
            "committee_$_management_level" not in instance
            and "committee_ids" not in instance
        ):
            return super().update_instance(instance)

        user = self.datastore.get(
            FullQualifiedId(Collection("user"), instance["id"]),
            mapped_fields=["committee_ids", "committee_$_management_level"],
        )
        old_committee_ids = set(user.get("committee_ids", ()))
        old_manager_ids = set(map(int, user.get("committee_$_management_level", ())))
        inst_new_manager_ids = {
            int(pair[0])
            for pair in instance.get("committee_$_management_level", {}).items()
            if pair[1]
        }
        if "committee_ids" in instance:
            inst_committee_ids = set(instance.get("committee_ids", ()))
            instance["committee_ids"] = list(inst_committee_ids | inst_new_manager_ids)
        else:
            instance["committee_ids"] = list(old_committee_ids | inst_new_manager_ids)
        if cml_to_remove := (
            old_committee_ids - set(instance["committee_ids"]) & old_manager_ids
        ):
            cml_to_remove_dict = {
                str(committee_id): None for committee_id in cml_to_remove
            }
            instance.setdefault("committee_$_management_level", {}).update(
                cml_to_remove_dict
            )

        return super().update_instance(instance)
