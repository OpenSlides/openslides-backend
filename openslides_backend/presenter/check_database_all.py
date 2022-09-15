from typing import Any, Dict

import fastjsonschema
from datastore.shared.util import strip_reserved_fields

from openslides_backend.migrations import get_backend_migration_index

from ..models.checker import Checker, CheckException
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..shared.exceptions import PermissionDenied
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

check_database_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "check database",
        "description": "check database",
        "properties": {},
    }
)


@register_presenter("check_database_all")
class CheckDatabaseAll(BasePresenter):
    """Check Database All gets all non-deleted meetings, exports them,
    and check them with the checker."""

    schema = check_database_schema

    def get_result(self) -> Any:
        # check permissions
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            msg = "You are not allowed to perform presenter check_database."
            msg += f" Missing permission: {OrganizationManagementLevel.SUPERADMIN}"
            raise PermissionDenied(msg)

        export = self.get_everything()
        checker = Checker(
            data=export,
            mode="all",
        )
        try:
            checker.run_check()
            return {"ok": True}
        except CheckException as ce:
            return {"ok": False, "errors": str(ce)}

    def get_everything(self) -> Dict[str, Any]:
        everything = self.datastore.get_everything()
        export: Dict[str, Any] = {
            collection: self.remove_meta_fields(everything[collection])
            for collection in everything
        }
        export["_migration_index"] = get_backend_migration_index()
        return export

    def remove_meta_fields(self, res: Dict[int, Any]) -> Dict[str, Any]:
        dict_without_meta_fields = {}
        for key in res:
            strip_reserved_fields(res[key])
            dict_without_meta_fields[str(key)] = res[key]
        return dict_without_meta_fields
