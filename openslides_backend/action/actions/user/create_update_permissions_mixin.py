from collections import defaultdict
from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ....models.models import User
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import MissingPermission, PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.util_dict_sets import get_set_from_dict_by_fieldlist
from .user_scope_permission_check_mixin import UserScope, UserScopePermissionCheckMixin


class PermissionVarStore:
    def __init__(self, datastore: DatastoreService, user_id: int) -> None:
        self.datastore = datastore
        self.user_id = user_id
        self._cml_replacement_min_can_manage = [
            f"committee_${replacement}_management_level"
            for replacement in cast(
                List[str], User.committee__management_level.replacement_enum
            )
            if CommitteeManagementLevel(replacement)
            >= CommitteeManagementLevel.CAN_MANAGE
        ]
        self.user = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id),
            [
                "organization_management_level",
                "group_$_ids",
                "committee_ids",
                *self._cml_replacement_min_can_manage,
            ],
        )
        self.user_oml = OrganizationManagementLevel(
            self.user.get("organization_management_level")
        )
        self._user_committees: Optional[Set[int]] = None
        self._user_meetings: Optional[Set[int]] = None

    @property
    def user_committees(self) -> Set[int]:
        """Set of committee-ids where the request user has manage rights"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees

    @property
    def user_committees_meetings(self) -> Set[int]:
        """Set of meetings where the request user has manage rights from committee"""
        if self._user_committees is None:
            (
                self._user_committees,
                self._user_committees_meetings,
            ) = self._get_user_committees_and_meetings()
        return self._user_committees_meetings

    @property
    def user_meetings(self) -> Set[int]:
        """Set of meetings where the request user has user.can_manage permissions"""
        if self._user_meetings is None:
            self._user_meetings = self._get_user_meetings_with_user_can_manage(
                self.user.get("group_$_ids", [])
            )
        return self._user_meetings

    def _get_user_committees_and_meetings(self) -> Tuple[Set[int], Set[int]]:
        """
        Returns a set of committees and a set of meetings
        belonging to those committees, where the request user has minimum
        CommitteeManagementLevel.CAN_MANAGE and is member of committee_id,
        """
        user_committees = get_set_from_dict_by_fieldlist(
            self.user, self._cml_replacement_min_can_manage
        )
        if user_committees:
            committees_d = (
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            Collection("committee"),
                            list(user_committees),
                            ["meeting_ids"],
                        )
                    ]
                )
                .get(Collection("committee"), {})
                .values()
            )
            user_meetings = reduce(
                lambda i1, i2: i1 | i2,
                [
                    set(committee.get("meeting_ids", set()))
                    for committee in committees_d
                ],
            )
        else:
            user_meetings = set()
        return user_committees, user_meetings

    def _get_user_meetings_with_user_can_manage(
        self, meeting_ids: List[str] = []
    ) -> Set[int]:
        """
        Returns a set of meetings, where the request user has user.can_manage permissions
        """
        user_meetings = set()
        if meeting_ids:
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), self.user_id),
                [f"group_${meeting_id}_ids" for meeting_id in meeting_ids],
            )
            all_groups: List[int] = []
            for groups in user.values():
                if type(groups) == list:
                    all_groups.extend(groups)
            groups = (
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            Collection("group"),
                            list(all_groups),
                            ["meeting_id", "permissions", "admin_group_for_meeting_id"],
                        )
                    ]
                )
                .get(Collection("group"), {})
                .values()
            )

            for group in groups:
                if Permissions.User.CAN_MANAGE in group.get(
                    "permissions", []
                ) or group.get("admin_group_for_meeting_id"):
                    user_meetings.add(group.get("meeting_id"))

        return user_meetings


class CreateUpdatePermissionsMixin(UserScopePermissionCheckMixin):
    field_rights: Dict[str, list] = {
        "A": [
            "title",
            "first_name",
            "last_name",
            "username",
            "is_active",
            "is_physical_person",
            "default_password",
            "can_change_own_password",
            "gender",
            "pronoun",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
        ],
        "B": [
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "is_present_in_meeting_ids",
        ],
        "C": ["group_$_ids"],
        "D": ["committee_ids", "committee_$_management_level"],
        "E": ["organization_management_level"],
        "F": ["is_demo_user"],
    }

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """
        Checks the permissions on a per field and user.scope base, details see
        https://github.com/OpenSlides/OpenSlides/wiki/user.update or user.create
        The fields groups and their necessary permissions are also documented there.
        """
        self.assert_not_anonymous()

        permstore = PermissionVarStore(self.datastore, self.user_id)
        if permstore.user_oml == OrganizationManagementLevel.SUPERADMIN:
            return

        self._check_for_higher_OML(permstore, instance)
        self._check_OML_in_instance(permstore, instance)
        actual_group_fields = self._get_actual_grouping_from_instance(instance)

        # Ordered by supposed velocity advantages. Changing order only can effect the sequence of detected errors for tests
        self.check_group_E(permstore, actual_group_fields["E"])
        self.check_group_D(permstore, actual_group_fields["D"], instance)
        self.check_group_C(permstore, actual_group_fields["C"], instance)
        self.check_group_B(permstore, actual_group_fields["B"], instance)
        self.check_group_A(permstore, actual_group_fields["A"], instance)
        self.check_group_F(actual_group_fields["F"])

    def check_group_A(
        self, permstore: PermissionVarStore, fields: List[str], instance: Dict[str, Any]
    ) -> None:
        """Check Group A common fields: Depending on scope of user to act on"""
        if (
            not fields
            or permstore.user_oml >= OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return

        if uid := instance.get("id"):
            self.apply_instance(instance)

        scope, scope_id = self.get_user_scope(uid, None if uid else instance)
        if scope == UserScope.Organization:
            raise MissingPermission({OrganizationManagementLevel.CAN_MANAGE_USERS: 1})
        elif scope == UserScope.Committee:
            if scope_id not in permstore.user_committees:
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                        CommitteeManagementLevel.CAN_MANAGE: scope_id,
                    }
                )
        elif (
            scope_id not in permstore.user_committees_meetings
            and scope_id not in permstore.user_meetings
        ):
            meeting = self.datastore.fetch_model(
                FullQualifiedId(Collection("meeting"), scope_id), ["committee_id"]
            )
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_USERS: 1,
                    CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                    Permissions.User.CAN_MANAGE: scope_id,
                }
            )

    def check_group_B(
        self, permstore: PermissionVarStore, fields: List[str], instance: Dict[str, Any]
    ) -> None:
        """Check Group B meeting template fields: Only meeting.permissions for each meeting"""
        if fields:
            meeting_ids = self._meetings_from_group_B_fields_from_instance(
                fields, instance
            )
            if diff := meeting_ids - permstore.user_meetings:
                raise MissingPermission(
                    {Permissions.User.CAN_MANAGE: meeting_id for meeting_id in diff}
                )

    def check_group_C(
        self, permstore: PermissionVarStore, fields: List[str], instance: Dict[str, Any]
    ) -> None:
        """Check Group C group_$_ids: OML, CML or meeting.permissions for each meeting"""
        if fields and permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS:
            touch_meeting_ids: Set[int] = set(
                map(int, instance.get("group_$_ids", dict()).keys())
            )
            # Check permission for each change operation/meeting
            if diff := touch_meeting_ids - permstore.user_committees_meetings:
                if diff := diff - permstore.user_meetings:
                    raise PermissionDenied(
                        f"The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committees of following meetings or Permission user.can_manage for meetings {diff}"
                    )

    def check_group_D(
        self, permstore: PermissionVarStore, fields: List[str], instance: Dict[str, Any]
    ) -> None:
        """Check Group D committee-related fields: OML or CML level for each committee"""
        if fields and permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS:
            committees = self._get_all_committees_from_instance(instance)
            if diff := committees - permstore.user_committees:
                raise MissingPermission(
                    {
                        CommitteeManagementLevel.CAN_MANAGE: committee_id
                        for committee_id in diff
                    }
                )

    def check_group_E(self, permstore: PermissionVarStore, fields: List[str]) -> None:
        """Check Group E organization_management_level: OML level necessary"""
        if fields and permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS:
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)

    def check_group_F(self, fields: List[str]) -> None:
        """Group F: OML SUPERADMIN necessary, which is checked before"""
        if fields:
            raise MissingPermission(OrganizationManagementLevel.SUPERADMIN)

    def _check_for_higher_OML(
        self, permstore: PermissionVarStore, instance: Dict[str, Any]
    ) -> None:
        if "id" in instance:
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), instance["id"]),
                ["organization_management_level"],
            )
            if (
                OrganizationManagementLevel(user.get("organization_management_level"))
                > permstore.user_oml
            ):
                raise PermissionDenied(
                    f"Your organization management level is not high enough to change a user with a Level of {user.get('organization_management_level')}!"
                )

    def _check_OML_in_instance(
        self, permstore: PermissionVarStore, instance: Dict[str, Any]
    ) -> None:
        if "organization_management_level" in instance:
            if (
                OrganizationManagementLevel(instance["organization_management_level"])
                > permstore.user_oml
            ):
                raise PermissionDenied(
                    f"Your organization management level is not high enough to set a Level of {instance['organization_management_level']}!"
                )

    def _get_actual_grouping_from_instance(
        self, instance: Dict[str, Any]
    ) -> Dict[str, list]:
        """
        Returns a dictionary with an entry for each field group A-E with
        a list of fields from payload instance.
        The field groups A-F refer to https://github.com/OpenSlides/OpenSlides/wiki/user.create
        or user.update
        """
        act_grouping: Dict[str, list] = defaultdict(list)
        for key, _ in instance.items():
            for group in "ABCDEF":
                if key in self.field_rights[group]:
                    act_grouping[group].append(key)
                    break
            else:
                if key not in ["id"]:
                    raise PermissionDenied(
                        f"There is no field group for field {key} in payload"
                    )
        return act_grouping

    def _get_all_committees_from_instance(self, instance: Dict[str, Any]) -> Set[int]:
        """
        Gets a Set of all committees from the instance regarding committees from group D.
        To get committees, that should be removed from cml, the user must be read.
        """
        right_list = instance.get("committee_$_management_level", {}).keys()
        committees = set(
            [
                committee_id
                for committees in instance.get(
                    "committee_$_management_level", {}
                ).values()
                for committee_id in committees
            ]
        )
        # In case of create there is no id, in case of update the user can remove committees only with the committee right
        if instance_user_id := instance.get("id"):
            cml_fields = [
                f"committee_${replacement}_management_level"
                for replacement in right_list
            ]
            user = self.datastore.get(
                FullQualifiedId(Collection("user"), instance_user_id),
                [*cml_fields],
            )
            committees_existing = get_set_from_dict_by_fieldlist(user, cml_fields)
            # Just changes with ^ symmetric_difference operat
            committees = committees ^ committees_existing
        return committees

    def _meetings_from_group_B_fields_from_instance(
        self, fields_to_search_for: List[str], instance: Dict[str, Any]
    ) -> Set[int]:
        """
        Gets a set of all meetings from the fields of group B in instance
        """
        meetings: Set[int] = set()
        for field in fields_to_search_for:
            if "_$" in field:
                meetings.update(map(int, instance.get(field, dict()).keys()))
        return meetings
