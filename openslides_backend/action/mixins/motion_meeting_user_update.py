from openslides_backend.models.base import Model

from ..generics.update import UpdateAction
from ..util.default_schema import DefaultSchema


def build_motion_meeting_user_update_action(
    ModelClass: type[Model],
) -> type[UpdateAction]:
    class BaseMotionMeetingUserUpdateAction(UpdateAction):
        model = ModelClass()
        schema = DefaultSchema(ModelClass()).get_update_schema(
            required_properties=[
                "weight",
            ],
        )

    return BaseMotionMeetingUserUpdateAction
