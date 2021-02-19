from ....models.models import Projector
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector.delete")
class ProjectorDelete(DeleteAction):
    """
    Action to delete a projector.
    """
    
    model = Projector()
    schema = DefaultSchema(Projector()).get_delete_schema()
    
