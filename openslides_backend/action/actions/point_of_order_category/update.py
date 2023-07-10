from ....models.models import PointOfOrderCategory
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("point_of_order_category.update")
class PointOfOrderCategoryUpdate(UpdateAction):
    """
    Action to update a point of order category.
    """

    model = PointOfOrderCategory()
    schema = DefaultSchema(PointOfOrderCategory()).get_update_schema(
        optional_properties=["text", "rank"]
    )
    permission = Permissions.Meeting.CAN_MANAGE_SETTINGS
