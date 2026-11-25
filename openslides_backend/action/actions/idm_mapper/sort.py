from ....models.models import IdmMapper
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("idm_mapper.sort")
class IdmMapperSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort idm_mappers.
    """

    model = IdmMapper()
    schema = DefaultSchema(IdmMapper()).get_linear_sort_schema("idm_mapper_ids", None)
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(instance["idm_mapper_ids"])
