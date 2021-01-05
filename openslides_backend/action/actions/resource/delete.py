from ....models.models import Resource
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("resource.delete")
class ResourceDelete(DeleteAction):
    """
    Action to delete a resource.
    """

    model = Resource()
    schema = DefaultSchema(Resource()).get_delete_schema()
