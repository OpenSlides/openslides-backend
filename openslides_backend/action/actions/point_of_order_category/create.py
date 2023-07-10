from ....models.models import PointOfOrderCategory
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("point_of_order_category.create")
class PointOfOrderCategoryCreate(CreateAction):
    """
    Action to create a point of order category.
    """

    model = PointOfOrderCategory()
    schema = DefaultSchema(PointOfOrderCategory()).get_create_schema(
        required_properties=["text", "rank", "meeting_id"],
    )
    permission = Permissions.Meeting.CAN_MANAGE_SETTINGS
