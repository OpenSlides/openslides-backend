from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, cast

from ...services.datastore.interface import DatastoreService, GetManyRequest
from ..patterns import Collection, FullQualifiedId


class UserScope(int, Enum):
    Meeting = 1
    Committee = 2
    Organization = 3


class UserScopeMixin:

    datastore: DatastoreService

    def get_user_scope(
        self, id: Optional[int] = None, instance: Optional[Dict[str, Any]] = None
    ) -> Tuple[UserScope, int]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting, committee or organization).
        """
        meetings: List[int] = []

        if instance:
            meetings = list(map(int, instance.get("group_$_ids", {}).keys()))
            committees_manager = set(
                map(int, instance.get("committee_$_management_level", {}).keys())
            )
        elif id:
            user = self.datastore.fetch_model(
                FullQualifiedId(Collection("user"), id),
                ["meeting_ids", "committee_$_management_level"],
            )
            meetings = user.get("meeting_ids", [])
            committees_manager = set(
                map(int, user.get("committee_$_management_level", []))
            )
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("meeting"),
                    meetings,
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get(Collection("meeting"), {})
        committees_of_meetings = set(
            meeting_data.get("committee_id")
            for _, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        )
        committees = list(committees_manager | committees_of_meetings)
        meetings_committee = {
            meeting_id: meeting_data.get("committee_id")  # type: ignore
            for meeting_id, meeting_data in result.items()
            if meeting_data.get("is_active_in_organization_id")
        }

        if len(meetings_committee) == 1 and len(committees) == 1:
            return UserScope.Meeting, next(iter(meetings_committee))
        elif len(committees) == 1:
            return UserScope.Committee, cast(int, committees[0])
        return UserScope.Organization, 1
