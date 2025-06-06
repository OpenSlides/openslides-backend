from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportRow, ImportState
from ...util.register import register_action
from .base_import import BaseUserImport


@register_action("account.import")
class AccountImport(BaseUserImport):
    """
    Action to import a result from the import_preview.
    """

    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    import_name = "account"

    def validate_entry(self, row: ImportRow) -> None:
        super().validate_entry(row)
        if not self.check_field_failures(row["data"], row["messages"], "IJ"):
            row["state"] = ImportState.ERROR

        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR
