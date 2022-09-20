from typing import Any, Dict, List, Optional, Set

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import PermissionException
from ....shared.patterns import ID_REGEX, fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .set_present import UserSetPresentAction
from .user_mixin import LimitOfUserMixin, UserMixin


@register_action("user.update")
class UserUpdate(
    UserMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
    LimitOfUserMixin,
):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "pronoun",
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
        additional_optional_fields={
            "presence": {
                "type": "object",
                "additionalProperties": False,
                "patternProperties": {ID_REGEX: "boolean"},
            }
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id("user", instance["id"]),
            mapped_fields=[
                "is_active",
                "organization_management_level",
            ],
        )
        if (
            instance["id"] == self.user_id
            and user.get("organization_management_level")
            == OrganizationManagementLevel.SUPERADMIN
        ):
            if (
                "organization_management_level" in instance
                and instance.get("organization_management_level")
                != OrganizationManagementLevel.SUPERADMIN
            ):
                raise PermissionException(
                    "A user is not allowed to withdraw his own 'superadmin'-Organization-Management-Level."
                )
            if "is_active" in instance and instance.get("is_active") is not True:
                raise PermissionException(
                    "A superadmin is not allowed to set himself inactive."
                )
        if instance.get("is_active") and not user.get("is_active"):
            self.check_limit_of_user(1)

        presence = instance.pop("presence", None)
        if presence:
            action_payload = [
                {
                    "id": instance["id"],
                    "meeting_id": int(meeting_id),
                    "present": present,
                }
                for meeting_id, present in presence.items()
            ]
            self.execute_other_action(UserSetPresentAction, action_payload)
        return instance

    def get_history_information(self) -> Optional[List[str]]:
        informations: List[str] = []

        # User updated
        for instance in self.instances:
            instance_fields = set(instance.keys())

            update_fields = set(
                [
                    "title",
                    "first_name",
                    "last_name",
                    "email",
                    "username",
                    "default_structure_level",
                    "default_number",
                    "default_vote_weight",
                ]
            )
            if instance_fields & update_fields:
                informations.append("User updated")
                break

        # User updated in meeting x
        all_meetings: List[Set[str]] = []
        for instance in self.instances:
            meeting_ids: Set[str] = set()
            for field in ("structure_level_$", "number_$", "vote_weight_$"):
                if field in instance:
                    meeting_ids.update(instance[field] or set())
            all_meetings.append(meeting_ids)
        if any(all_meetings):
            self.add_to_history(
                informations,
                all_meetings,
                "User updated in meeting {}",
                "User updated in multiple meetings",
            )

        # Group x added/removed
        all_groups_added: List[Set[int]] = []
        all_groups_removed: List[Set[int]] = []
        for instance in self.instances:
            if "group_$_ids" in instance:
                group_ids_from_instance = self.get_group_ids_from_instance(instance)
                group_ids_from_db = self.get_group_ids_from_db(instance)
                added = group_ids_from_instance - group_ids_from_db
                removed = group_ids_from_db - group_ids_from_instance
                all_groups_added.append(added)
                all_groups_removed.append(removed)
        check_added = any(all_groups_added)
        check_removed = any(all_groups_removed)
        if check_added and check_removed:
            informations.append("Groups changed")
        elif check_added:
            self.add_to_history(
                informations, all_groups_added, "Group {} added", "Groups changed"
            )
        elif check_removed:
            self.add_to_history(
                informations, all_groups_removed, "Group {} removed", "Groups changed"
            )

        # OML/CML changed
        for instance in self.instances:
            if (
                "organization_management_level" in instance
                or "committee_$_management_level" in instance
            ):
                informations.append("OML/CML changed")
                break

        # Set (in)active
        for instance in self.instances:
            if "is_active" in instance:
                informations.append("Set (in)active")
                break

        return informations

    def add_to_history(
        self,
        informations: List[str],
        data: List[Set[Any]],
        single_msg: str,
        multi_msg: str,
    ) -> None:
        # assert data not empty
        for entries in data:
            if entries:
                entry_id = list(entries)[0]
                break

        if all([set([entry_id]) == entries for entries in data]):
            informations.append(single_msg.format(entry_id))
        else:
            informations.append(multi_msg)

    def get_group_ids_from_db(self, instance: Dict[str, Any]) -> Set[int]:
        user_fqid = fqid_from_collection_and_id("user", instance["id"])
        user1 = self.datastore.get(user_fqid, ["group_$_ids"], use_changed_models=False)
        if not user1.get("group_$_ids"):
            return set()
        # You can give partial group_$_ids in the instance.
        # so groups of meetings, which meeting is not in instance,
        # doesn't count.
        fields = [
            f"group_${meeting_id}_ids"
            for meeting_id in user1["group_$_ids"]
            if f"group_${meeting_id}_ids" in instance
        ]
        group_ids: Set[int] = set()
        user2 = self.datastore.get(user_fqid, fields, use_changed_models=False)
        for field in fields:
            group_ids.update(user2.get(field) or [])
        return group_ids

    def get_group_ids_from_instance(self, instance: Dict[str, Any]) -> Set[int]:
        fields = [
            f"group_${meeting_id}_ids" for meeting_id in (instance["group_$_ids"] or [])
        ]
        group_ids: Set[int] = set()
        for field in fields:
            group_ids.update(instance.get(field) or [])
        return group_ids
