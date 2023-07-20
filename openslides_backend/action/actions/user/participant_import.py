from ....permissions.management_levels import OrganizationManagementLevel
from ...util.register import register_action
from .base_import import BaseUserImport


@register_action("participant.import")
class ParticipantImport(BaseUserImport):
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    import_name = "participant"
