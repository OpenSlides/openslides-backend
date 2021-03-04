from typing import Any, Dict, Type

from ....models.models import Topic
from ...action import Action
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItemMixin,
    agenda_creation_properties,
)
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)


@register_action("topic.create")
class TopicCreate(
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    CreateActionWithListOfSpeakersMixin,
):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_create_schema(
        required_properties=["meeting_id", "title"],
        optional_properties=["text", "attachment_ids"],
        additional_optional_fields=agenda_creation_properties,
    )
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]

    def check_dependant_action_execution_agenda_item(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        """
        We always create an agenda item for each topic regardless of
        the given action data or metting settings.
        """
        return True
