from openslides_backend.models.base import Model

from ...models.models import Motion
from ...permissions.permissions import Permissions
from ...shared.filters import And, FilterOperator
from ..generics.update import UpdateAction
from ..mixins.linear_sort_mixin import LinearSortMixin
from ..mixins.singular_action_mixin import SingularActionMixin
from ..util.default_schema import DefaultSchema
from ..util.typing import ActionData


def build_motion_meeting_user_sort_action(
    ModelClass: type[Model], field: str
) -> type[UpdateAction]:
    class BaseMotionMeetingUserSortAction(
        LinearSortMixin, SingularActionMixin, UpdateAction
    ):
        """
        Action to sort motion comment sections.
        """

        model = ModelClass()
        schema = DefaultSchema(ModelClass()).get_linear_sort_schema(field, "motion_id")
        permission = Permissions.Motion.CAN_MANAGE_METADATA
        permission_model = Motion()
        permission_id = "motion_id"

        def get_updated_instances(self, action_data: ActionData) -> ActionData:
            action_data = super().get_updated_instances(action_data)
            # Action data is an iterable with exactly one item
            instance = next(iter(action_data))
            meeting_id = self.get_meeting_id(instance)
            yield from self.sort_linear(
                instance[field],
                And(
                    FilterOperator("motion_id", "=", instance["motion_id"]),
                    FilterOperator("meeting_id", "=", meeting_id),
                ),
            )

    return BaseMotionMeetingUserSortAction
