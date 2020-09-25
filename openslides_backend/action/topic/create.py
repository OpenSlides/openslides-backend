from typing import Any, Dict, Type

from ...models.topic import Topic
from ..action import register_action
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItem,
    agenda_creation_properties,
)
from ..base import Action
from ..default_schema import DefaultSchema

create_schema = DefaultSchema(Topic()).get_create_schema(
    properties=["meeting_id", "title", "text", "attachment_ids"],
    required_properties=["meeting_id", "title"],
)

create_schema["items"]["properties"].update(agenda_creation_properties)


@register_action("topic.create")
class TopicCreate(CreateActionWithAgendaItem):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = create_schema

    def check_dependant_action_execution(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        """
        We always create an agenda item for each topic regardless of
        payload or metting settings.
        """
        return True
