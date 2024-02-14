from openslides_backend.action.util.action_type import ActionType

from ....models.models import StructureLevelListOfSpeakers
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level_list_of_speakers.delete", ActionType.BACKEND_INTERNAL)
class StructureLevelListOfSpeakersDeleteAction(DeleteAction):
    model = StructureLevelListOfSpeakers()
    schema = DefaultSchema(StructureLevelListOfSpeakers()).get_delete_schema()
