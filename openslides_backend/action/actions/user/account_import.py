from ....permissions.management_levels import OrganizationManagementLevel
from ...util.register import register_action
from .base_import import BaseUserImport


@register_action("account.import")
class AccountImport(BaseUserImport):
    """
    Action to import a result from the action_worker.
    """

    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    import_name = "account"
