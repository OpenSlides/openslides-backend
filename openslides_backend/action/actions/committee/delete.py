from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.delete")
class CommitteeDeleteAction(DeleteAction):
    """
    Action to delete a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
