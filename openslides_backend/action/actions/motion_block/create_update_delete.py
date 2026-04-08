from ....models.models import MotionBlock
from ....permissions.permissions import Permissions
from ...action_set import ActionSet
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItemMixin,
    agenda_creation_properties,
)
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)


class MotionBlockCreate(
    SequentialNumbersMixin,
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    CreateActionWithListOfSpeakersMixin,
):
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]


@register_action_set("motion_block")
class MotionBlockActionSet(ActionSet):
    """
    Actions to create, update and delete motion blocks.
    """

    model = MotionBlock()
    create_schema = DefaultSchema(MotionBlock()).get_create_schema(
        required_properties=["title", "meeting_id"],
        optional_properties=["internal"],
        additional_optional_fields=agenda_creation_properties,
    )
    update_schema = DefaultSchema(MotionBlock()).get_update_schema(
        optional_properties=["title", "internal", "motion_ids"]
    )
    delete_schema = DefaultSchema(MotionBlock()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE

    CreateActionClass = MotionBlockCreate
