from ....models.models import Option
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("option.delete", action_type=ActionType.BACKEND_INTERNAL)
class OptionDelete(DeleteAction):
    """
    Action to delete options.
    """

    model = Option()
    schema = DefaultSchema(Option()).get_delete_schema()
