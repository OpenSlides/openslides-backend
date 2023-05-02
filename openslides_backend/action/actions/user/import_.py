from typing import Any, Dict, List

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportMixin, ImportStatus
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .update import UserUpdate
from .user_mixin import DuplicateCheckMixin


@register_action("user.import")
class UserImport(DuplicateCheckMixin, ImportMixin):
    """
    Action to import a result from the action_worker.
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id), ["result"]
        )
        if (worker.get("result") or {}).get("import") != "account":
            raise ActionException("Wrong id doesn't point on account import data.")

        # handle abort in on_success
        if not instance["import"]:
            return {}

        # init duplicate mixin
        data = worker.get("result", {}).get("rows", [])
        for entry in data:
            # Revert username-info and default-password-info
            for field in ("username", "default_password"):
                if field in entry["data"]:
                    entry["data"][field] = entry["data"][field]["value"]
            if entry["status"] == ImportStatus.ERROR:
                raise ActionException("Error in import.")

        search_data_list = [
            {
                field: entry["data"].get(field, "")
                for field in ("username", "first_name", "last_name", "email")
            }
            for entry in data
        ]
        self.init_duplicate_set(search_data_list)

        # Recheck and update data, update needs "id"
        create_action_payload: List[Dict[str, Any]] = []
        update_action_payload: List[Dict[str, Any]] = []
        for payload_index, entry in enumerate(data):
            if entry["status"] == ImportStatus.NEW:
                if not entry["data"].get("username"):
                    raise ActionException("Error: could not find username")
                elif self.check_username_for_duplicate(
                    entry["data"]["username"], payload_index
                ):
                    raise ActionException(
                        "Error: want to create a new user, but username already exists."
                    )
                else:
                    create_action_payload.append(entry["data"])
            elif entry["status"] == ImportStatus.DONE:
                search_data = self.get_search_data(payload_index)
                if not entry["data"].get("username"):
                    raise ActionException("Error: could not find username")
                elif not self.check_username_for_duplicate(
                    entry["data"]["username"], payload_index
                ):
                    raise ActionException(
                        "Error: want to update, but missing user in db."
                    )
                elif search_data is None:
                    raise ActionException(
                        "Error: want to update, but found search data are wrong."
                    )
                elif search_data["username"] != entry["data"]["username"]:
                    raise ActionException(
                        "Error: want to update, but found search data doesn't match."
                    )

                else:
                    del entry["data"]["username"]
                    update_action_payload.append(entry["data"])
            else:
                raise ActionException("Error in import.")

        # execute the actions
        if create_action_payload:
            self.execute_other_action(UserCreate, create_action_payload)
        if update_action_payload:
            self.execute_other_action(UserUpdate, update_action_payload)
        return {}
