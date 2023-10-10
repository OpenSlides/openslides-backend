from typing import Any, Dict

import fastjsonschema
from datastore.shared.util import is_reserved_field

from openslides_backend.migrations import get_backend_migration_index

from ..models.checker import Checker, CheckException
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..services.datastore.interface import DatastoreService
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


def check_everything(datastore: DatastoreService) -> None:
    result = datastore.get_everything()
    data: Dict[str, Any] = {
        collection: {
            str(id): {
                field: value
                for field, value in model.items()
                if not is_reserved_field(field)
            }
            for id, model in models.items()
        }
        for collection, models in result.items()
        if collection not in ["action_worker", "import_preview"]
    }
    data["_migration_index"] = get_backend_migration_index()
    Checker(
        data=data,
        mode="all",
    ).run_check()


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

        try:
            check_everything(self.datastore)
            return {"ok": True}
        except CheckException as ce:
            return {"ok": False, "errors": str(ce)}
