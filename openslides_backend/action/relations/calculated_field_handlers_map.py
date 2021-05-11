from collections import defaultdict
from typing import Dict, List, Type

from ...models.fields import Field
from ...models.models import Group
from .calculated_field_handler import CalculatedFieldHandler
from .meeting_user_ids_handler import MeetingUserIdsHandler

# This maps all CalculatedFieldsHandlers to the fields for which they need to get the
# updates. Fill this map if you add more handlers.
handler_to_field_map: Dict[Type[CalculatedFieldHandler], List[Field]] = {
    MeetingUserIdsHandler: [Group.user_ids]
}
calculated_field_handlers_map: Dict[
    Field, List[Type[CalculatedFieldHandler]]
] = defaultdict(list)


def prepare_calculated_field_handlers_map() -> None:
    for handler_class, fields in handler_to_field_map.items():
        for field in fields:
            calculated_field_handlers_map[field].append(handler_class)


prepare_calculated_field_handlers_map()
