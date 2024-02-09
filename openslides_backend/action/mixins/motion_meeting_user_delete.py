from openslides_backend.models.base import Model

from ...permissions.permissions import Permissions
from ..generics.delete import DeleteAction
from ..util.default_schema import DefaultSchema


def build_motion_meeting_user_delete_action(
    ModelClass: type[Model],
) -> type[DeleteAction]:
    class BaseMotionMeetingUserDeleteAction(DeleteAction):
        model = ModelClass()
        schema = DefaultSchema(ModelClass()).get_delete_schema()
        permission = Permissions.Motion.CAN_MANAGE_METADATA

    return BaseMotionMeetingUserDeleteAction
