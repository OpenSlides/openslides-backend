from typing import Any, Dict

import fastjsonschema
from datastore.shared.util import is_reserved_field

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

ALL_COLLECTIONS = [
    "meeting",
    "group",
    "personal_note",
    "tag",
    "agenda_item",
    "list_of_speakers",
    "speaker",
    "topic",
    "motion",
    "motion_submitter",
    "motion_comment",
    "motion_comment_section",
    "motion_category",
    "motion_block",
    "motion_change_recommendation",
    "motion_state",
    "motion_workflow",
    "motion_statute_paragraph",
    "poll",
    "option",
    "vote",
    "assignment",
    "assignment_candidate",
    "mediafile",
    "projector",
    "projection",
    "projector_message",
    "projector_countdown",
    "chat_group",
    "chat_message",
    "organization",
    "user",
    "organization_tag",
    "theme",
    "committee",
]


@register_presenter("check_database")
class CheckDatabase(BasePresenter):
    """Check Database gets all non-deleted meetings, exports them,
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

        export = self.get_all_database()
        checker = Checker(
            data=export,
            mode="all",
        )
        errors: str = ""
        try:
            checker.run_check()
        except CheckException as ce:
            errors = str(ce)
        if not errors:
            return {"ok": True, "errors": ""}
        return {"ok": False, "errors": errors}

    def get_all_database(self) -> Dict[str, Any]:
        export: Dict[str, Any] = {"_migration_index": get_backend_migration_index()}
        for collection in ALL_COLLECTIONS:
            export[collection] = remove_meta_fields(
                self.datastore.get_all(collection, [], lock_result=False)
            )
        return export


def remove_meta_fields(res: Dict[int, Any]) -> Dict[str, Any]:
    dict_without_meta_fields = {}
    for key in res:
        new_entry = {}
        for fieldname in res[key]:
            if not is_reserved_field(fieldname):
                new_entry[fieldname] = res[key][fieldname]
        dict_without_meta_fields[str(key)] = new_entry
    return dict_without_meta_fields
