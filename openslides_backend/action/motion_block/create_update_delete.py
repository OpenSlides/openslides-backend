from ...models.models import MotionBlock
from ..action_set import ActionSet
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItemMixin,
    agenda_creation_properties,
)
from ..agenda_item.create import AgendaItemCreate
from ..create_action_with_dependencies import CreateActionWithDependencies
from ..default_schema import DefaultSchema
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)
from ..register import register_action_set

create_schema = DefaultSchema(MotionBlock()).get_create_schema(
    required_properties=["title", "meeting_id"], optional_properties=["internal"],
)

create_schema["items"]["properties"].update(agenda_creation_properties)


class MotionBlockCreate(
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    CreateActionWithListOfSpeakersMixin,
):
    model = MotionBlock()
    schema = create_schema
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]


@register_action_set("motion_block")
class MotionBlockActionSet(ActionSet):
    """
    Actions to create, update and delete motion blocks.
    """

    model = MotionBlock()
    create_schema = create_schema
    update_schema = DefaultSchema(MotionBlock()).get_update_schema(
        optional_properties=["title", "internal", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionBlock()).get_delete_schema()

    CreateActionClass = MotionBlockCreate
