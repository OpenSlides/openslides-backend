from ....models.models import OrganisationTag
from ....permissions.management_levels import OrganisationManagementLevel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organisation_tag.delete")
class OrganisationTagDelete(DeleteAction):
    """
    Action to delete a organisation tag.
    """

    model = OrganisationTag()
    schema = DefaultSchema(OrganisationTag()).get_delete_schema()
    permission = OrganisationManagementLevel.CAN_MANAGE_ORGANISATION
