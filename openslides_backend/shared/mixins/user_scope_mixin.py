from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from ...models.models import Committee
from ...services.datastore.interface import DatastoreService, GetManyRequest
from ..patterns import Collection, FullQualifiedId
from ..util_dict_sets import get_set_from_dict_by_fieldlist, get_set_from_dict_from_dict


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
        meetings: Set[int] = set()
        committees_manager: Set[int] = set()
        cml_fields = [
            f"committee_${cml_field}_management_level"
            for cml_field in cast(
                List[str], Committee.user__management_level.replacement_enum
            )
        ]
        if instance:
            meetings.update(map(int, instance.get("group_$_ids", {}).keys()))
            committees_manager.update(
                get_set_from_dict_from_dict(instance, "committee_$_management_level")
            )
        if id:
            user = self.datastore.fetch_model(
                FullQualifiedId(Collection("user"), id),
                ["meeting_ids", *cml_fields],
            )
            meetings.update(user.get("meeting_ids", []))
            committees_manager.update(get_set_from_dict_by_fieldlist(user, cml_fields))
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("meeting"),
                    list(meetings),
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
