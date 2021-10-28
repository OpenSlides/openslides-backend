from ....models.models import Resource
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionMixin


@register_action("resource.delete")
class ResourceDelete(PermissionMixin, DeleteAction):
    """
    Action to delete a resource.
    """

    model = Resource()
    schema = DefaultSchema(Resource()).get_delete_schema()
    skip_archived_meeting_check = True
