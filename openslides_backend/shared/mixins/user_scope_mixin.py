from enum import Enum
from typing import Any, Dict, Optional, Set, Tuple, cast

from ...services.datastore.interface import DatastoreService, GetManyRequest
from ..exceptions import ServiceException
from ..patterns import fqid_from_collection_and_id


class UserScope(int, Enum):
    Meeting = 1
    Committee = 2
    Organization = 3


class UserScopeMixin:

    datastore: DatastoreService

    def get_user_scope(
        self, id_: Optional[int] = None, instance: Optional[Dict[str, Any]] = None
    ) -> Tuple[UserScope, int, str]:
        """
        Returns the scope of the given user id together with the relevant scope id (either meeting, committee or organization).
        and the oml-level of the user as string (Empty string, if no)
        """
        meetings: Set[int] = set()
        committees_manager: Set[int] = set()
        if not instance and not id_:
            raise ServiceException("There is no user_id given to get the user_scope!")
        if instance:
            meetings.update(map(int, instance.get("group_$_ids", {}).keys()))
            committees_manager.update(set(instance.get("committee_management_ids", [])))
            oml_right = instance.get("organization_management_level", "")
        if id_:
            user = self.datastore.get(
                fqid_from_collection_and_id("user", id_),
                [
                    "meeting_ids",
                    "organization_management_level",
                    "committee_management_ids",
                ],
            )
            meetings.update(user.get("meeting_ids", []))
            committees_manager.update(set(user.get("committee_management_ids") or []))
            oml_right = user.get("organization_management_level", "")
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list(meetings),
                    ["committee_id", "is_active_in_organization_id"],
                )
            ]
        ).get("meeting", {})
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
            return UserScope.Meeting, next(iter(meetings_committee)), oml_right
        elif len(committees) == 1:
            return UserScope.Committee, cast(int, committees[0]), oml_right
        return UserScope.Organization, 1, oml_right
