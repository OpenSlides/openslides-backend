from typing import Any, Dict, List, Set, Tuple, cast

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import (
    CommitteeManager,
    OrganisationManagementLevel,
    Permission,
    Permissions,
)
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class CreateUpdatePermissionsMixin(Action):
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
            CommitteeManager(),
            Permissions.User.CAN_MANAGE,
        ],
    }

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """
        Precondition:
         If there is more than one right sufficient for one field (Group C), the Meeting-Level-Permissions
         are expected to be the last in the field_rights list
        """
        if self.auth.is_anonymous(self.user_id):
            raise PermissionDenied("Anonymous user is not allowed to change user data.")

        user = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id),
            ["organisation_management_level", "committee_as_manager_ids"],
        )
        user_oml_level = user.get("organisation_management_level")
        if user_oml_level == OrganisationManagementLevel.SUPERADMIN:
            return

        user_oml_level_number = self._get_and_check_oml_level_number(
            cast(OrganisationManagementLevel, user_oml_level), instance
        )

        user_meetings = self._get_user_meetings_set(
            cast(List[int], user.get("committee_as_manager_ids", []))
        )
        necessary_permissions: Set[Tuple[Permission, int]] = set()
        missing_rights: Set[str] = set()
        potentially_missing_rights: Set[str] = set()

        for fieldname, value in instance.items():
            temp_right = False
            temp_missing_rights: Set[str] = set()
            for right in self.field_rights.get(fieldname, []):
                if type(right) == OrganisationManagementLevel:
                    if (
                        OrganisationManagementLevel.get_level_number(right)
                        > user_oml_level_number
                    ):
                        temp_missing_rights.add(str(right))
                    else:
                        temp_right = True
                        break
                elif type(right) == CommitteeManager:
                    result = {
                        int(meeting_id) for meeting_id in value.keys()
                    } - user_meetings
                    if result:
                        temp_missing_rights.add(f"{str(right)} for meetings {result}")
                    else:
                        temp_right = True
                        break
                else:
                    potentially_missing_rights = potentially_missing_rights.union(
                        temp_missing_rights
                    )
                    temp_missing_rights = set()
                    for meeting_id in value.keys():
                        necessary_permissions.add((right, int(meeting_id)))
            if not temp_right and temp_missing_rights:
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

    def _get_and_check_oml_level_number(
        self, user_oml_level: OrganisationManagementLevel, instance: Dict[str, Any]
    ) -> int:
        user_oml_level_number = OrganisationManagementLevel.get_level_number(
            cast(OrganisationManagementLevel, user_oml_level)
        )
        if (
            "organisation_management_level" in instance
            and OrganisationManagementLevel.get_level_number(
                instance["organisation_management_level"]
            )
            > user_oml_level_number
        ):
            raise PermissionDenied(
                f"Your Organisation Management Level is not high enough to set a Level of {instance['organisation_management_level']}!"
            )
        return user_oml_level_number

    def _get_user_meetings_set(self, committee_ids: List[int]) -> Set[int]:
        user_meetings = []
        if committee_ids:
            committees = (
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            Collection("committee"), committee_ids, ["meeting_ids"]
                        )
                    ]
                )
                .get(Collection("committee"), {})
                .values()
            )
            for committee in committees:
                user_meetings.extend(committee.get("meeting_ids", []))

        return set(user_meetings)
