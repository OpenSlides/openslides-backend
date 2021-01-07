from ....models.models import Option
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("option.delete")
class OptionDelete(DeleteAction):
    """
    Action to delete options.
    """

    model = Option()
    schema = DefaultSchema(Option()).get_delete_schema()
