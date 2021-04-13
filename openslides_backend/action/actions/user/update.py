from typing import Any, Dict, Set, Tuple, cast

from ....models.models import User
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import (
    OrganisationManagementLevel,
    Permission,
    Permissions,
)
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin
from .user_mixin import UserMixin


@register_action("user.update")
class UserUpdate(CheckTemporaryNoForInstanceMixin, UpdateAction, UserMixin):
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
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organisation_management_level",
            "committee_as_member_ids",
            "committee_as_manager_ids",
            "guest_meeting_ids",
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "group_$_ids",
        ],
    )

    field_rights: Dict[str, list] = {
        # Group A
        "username": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "title": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "first_name": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "last_name": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "is_active": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "is_physical_person": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "default_password": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "gender": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "email": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "default_number": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "default_structure_level": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "default_vote_weight": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "organisation_management_level": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "committee_as_member_ids": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "committee_as_manager_ids": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        "guest_meeting_ids": [OrganisationManagementLevel.CAN_MANAGE_USERS],
        # Group B
        "number_$": [Permissions.User.CAN_MANAGE],
        "structure_level_$": [Permissions.User.CAN_MANAGE],
        "vote_weight_$": [Permissions.User.CAN_MANAGE],
        "about_me_$": [Permissions.User.CAN_MANAGE],
        "comment_$": [Permissions.User.CAN_MANAGE],
        "vote_delegated_$_to_id": [Permissions.User.CAN_MANAGE],
        "vote_delegations_$_from_ids": [Permissions.User.CAN_MANAGE],
        # Group C
        "group_$_ids": [
            OrganisationManagementLevel.CAN_MANAGE_ORGANISATION,
            Permissions.User.CAN_MANAGE,
        ],
    }

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """
        Gather all necessary rights
        If there is more than one right sufficient for one field (Group C), the OrganisationManagementLevel-right
        is expected to be the first in the field_rights list
        """
        if self.auth.is_anonymous(self.user_id):
            raise PermissionDenied("Anonymous user is not allowed to update user data.")

        actual_oml_level = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id),
            ["organisation_management_level"],
        ).get("organisation_management_level")
        if actual_oml_level == OrganisationManagementLevel.SUPERADMIN:
            return

        actual_oml_level_number = OrganisationManagementLevel.get_level_number(
            cast(OrganisationManagementLevel, actual_oml_level)
        )
        if (
            "organisation_management_level" in instance
            and OrganisationManagementLevel.get_level_number(
                instance["organisation_management_level"]
            )
            > actual_oml_level_number
        ):
            raise PermissionDenied(
                f"Your Organisation Management Level is not high enough to set a Level of {instance['organisation_management_level']}!"
            )

        necessary_permissions: Set[Tuple[Permission, int]] = set()
        missing_rights: Set[str] = set()
        potentially_missing_rights: Set[str] = set()

        for fieldname, value in instance.items():
            oml_right = False
            temp_missing_rights: Set[str] = set()
            for right in self.field_rights.get(fieldname, []):
                if type(right) == OrganisationManagementLevel:
                    if (
                        OrganisationManagementLevel.get_level_number(right)
                        > actual_oml_level_number
                    ):
                        temp_missing_rights.add(str(right))
                    else:
                        oml_right = True
                        break
                else:
                    potentially_missing_rights = potentially_missing_rights.union(
                        temp_missing_rights
                    )
                    temp_missing_rights = set()
                    for meeting_id in value.keys():
                        necessary_permissions.add((right, int(meeting_id)))
            if not oml_right and temp_missing_rights:
                missing_rights = missing_rights.union(temp_missing_rights)

        if necessary_permissions:
            for right in necessary_permissions:
                permission, meeting_id = right
                if not has_perm(self.datastore, self.user_id, permission, meeting_id):
                    missing_rights.add(f"{str(permission)} for meeting {meeting_id}")

        if missing_rights:
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permissions {missing_rights}"
            if potentially_missing_rights:
                msg += f" or alternative {potentially_missing_rights}."
            raise PermissionDenied(msg)
