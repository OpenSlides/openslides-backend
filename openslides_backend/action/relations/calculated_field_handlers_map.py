from collections import defaultdict
from typing import Dict, List, Type

from ...models.fields import Field
from ...models.models import Group, MeetingUser, User
from .calculated_field_handler import CalculatedFieldHandler
from .meeting_user_ids_handler import MeetingUserIdsHandler
from .user_committee_calculate_handler import UserCommitteeCalculateHandler
from .user_meeting_ids_handler import UserMeetingIdsHandler

# This maps all CalculatedFieldsHandlers to the fields for which they need to get the
# updates. Fill this map if you add more handlers.
handler_to_field_map: Dict[Type[CalculatedFieldHandler], List[Field]] = {
    MeetingUserIdsHandler: [Group.meeting_user_ids],  # calcs meeting.user_ids
    UserMeetingIdsHandler: [MeetingUser.group_ids],  # calcs user.meeting_ids
    UserCommitteeCalculateHandler: [
        MeetingUser.group_ids,
        User.committee_management_ids,
    ],  # calcs user.committee_ids and committee.user_ids
}
calculated_field_handlers_map: Dict[Field, List[Type[CalculatedFieldHandler]]] = (
    defaultdict(list)
)


def prepare_calculated_field_handlers_map() -> None:
    for handler_class, fields in handler_to_field_map.items():
        for field in fields:
            calculated_field_handlers_map[field].append(handler_class)


prepare_calculated_field_handlers_map()
