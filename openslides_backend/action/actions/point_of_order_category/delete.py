from ....models.models import PointOfOrderCategory
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("point_of_order_category.delete")
class PointOfOrderCategoryDelete(DeleteAction):
    """
    Action to delete a point of order category.
    """

    model = PointOfOrderCategory()
    schema = DefaultSchema(PointOfOrderCategory()).get_delete_schema()
    permission = Permissions.Meeting.CAN_MANAGE_SETTINGS
