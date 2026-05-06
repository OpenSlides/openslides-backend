from typing import Literal

from openslides_backend.action.action import Action
from openslides_backend.shared.filters import And, FilterOperator, Or

from ...permissions.base_classes import Permission
from ...permissions.permission_helper import has_perm
from ...services.database.commands import GetManyRequest
from ...shared.exceptions import MissingPermission

DelegationBasedRestriction = Literal[
    "users_forbid_delegator_in_list_of_speakers",
    "users_forbid_delegator_as_submitter",
    "users_forbid_delegator_as_supporter",
]


class DelegationBasedRestrictionMixin(Action):
    def check_perm_and_delegator_restriction(
        self,
        perm: Permission,
        restriction: DelegationBasedRestriction,
        meeting_ids: list[int],
    ) -> list[int]:
        """
        Returns the list of meeting ids among the given meeting ids where the calling user has the permission,
        raises an exception if in any meeting the user doesn't have the permission and has his rights restricted by the delegator restriction.
        """
        has_perm_meetings: list[int] = []
        missing_perm_meetings: list[int] = []
        for meeting_id in meeting_ids:
            if has_perm(self.datastore, self.user_id, perm, meeting_id):
                has_perm_meetings.append(meeting_id)
            else:
                missing_perm_meetings.append(meeting_id)
        if len(missing_perm_meetings) and len(
            self.check_delegator_restriction(restriction, missing_perm_meetings)
        ):
            raise MissingPermission(perm)
        else:
            return has_perm_meetings

    def check_delegator_restriction(
        self,
        restriction: DelegationBasedRestriction,
        meeting_ids: list[int],
    ) -> list[int]:
        """
        Function to determine if a request user falls under the requirements for any of the delegation based restrictions in given meetings.
        Returns the meetings where this is the case.
        """
        if not len(meeting_ids):
            return []

        meeting_users = self.datastore.filter(
            "meeting_user",
            And(
                Or(
                    FilterOperator("meeting_id", "=", meeting_id)
                    for meeting_id in meeting_ids
                ),
                FilterOperator("user_id", "=", self.user_id),
                FilterOperator("vote_delegated_to_id", "!=", None),
            ),
            ["meeting_id"],
            lock_result=False,
        )
        if len(meeting_users):
            delegation_meeting_ids = [
                meeting_user["meeting_id"] for meeting_user in meeting_users.values()
            ]
            delegation_meetings = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting",
                        delegation_meeting_ids,
                        [restriction, "users_enable_vote_delegations"],
                    ),
                ],
                lock_result=False,
            )["meeting"]
            broken_meetings: list[int] = []
            for meeting_id, meeting in delegation_meetings.items():
                if meeting.get(restriction) and (
                    meeting.get("users_enable_vote_delegations")
                ):
                    broken_meetings.append(meeting_id)
            return broken_meetings
        return []
