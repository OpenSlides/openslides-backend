from typing import Any

from ....models.models import Topic
from ....permissions.permissions import Permissions
from ....shared.schema import id_list_schema
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
from ..meeting_mediafile.attachment_mixin import AttachmentMixin


@register_action("topic.create")
class TopicCreate(
    AttachmentMixin,
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
        optional_properties=["text"],
        additional_optional_fields={
            "attachment_mediafile_ids": id_list_schema,
            **agenda_creation_properties,
        },
    )
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]
    permission = Permissions.AgendaItem.CAN_MANAGE

    def check_dependant_action_execution_agenda_item(
        self, element: dict[str, Any], CreateActionClass: type[Action]
    ) -> bool:
        """
        We always create an agenda item for each topic regardless of
        the given action data or metting settings.
        """
        return True
