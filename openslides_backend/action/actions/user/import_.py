from typing import Any, Callable, Dict, List

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .create import UserCreate
from .json_upload import ImportStatus
from .update import UserUpdate
from .user_mixin import DuplicateCheckMixin


@register_action("user.import")
class UserImport(DuplicateCheckMixin, Action):
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
        self.init_duplicate_set()
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id), ["result"]
        )
        if (worker.get("result") or {}).get("import") != "account":
            raise ActionException("Wrong id doesn't point on account import data.")
        if instance["import"]:
            create_action_payload: List[Dict[str, Any]] = []
            update_action_payload: List[Dict[str, Any]] = []
            for entry in worker.get("result", {}).get("rows", []):
                if entry["status"] in (
                    ImportStatus.CREATE,
                    ImportStatus.UPDATE,
                ) and entry["data"].get("username"):
                    username = entry["data"]["username"]
                    data = entry["data"]
                    if self.check_username_for_duplicate(username):
                        id_ = self.username_to_id.get(username)
                        if not id_:
                            raise ActionException("Could not find id for username.")
                        del data["username"]
                        data["id"] = id_
                        update_action_payload.append(data)
                    else:
                        create_action_payload.append(data)
                elif entry["status"] in (ImportStatus.CREATE, ImportStatus.UPDATE):
                    data = entry["data"]
                    if self.check_name_and_email_for_duplicate(
                        data.get("first_name"), data.get("last_name"), data.get("email")
                    ):
                        id_ = self.names_and_email_to_id.get(
                            (
                                data.get("first_name"),
                                data.get("last_name"),
                                data.get("email"),
                            )
                        )
                        if not id_:
                            raise ActionException(
                                "Could not find id for names and email"
                            )
                        for field in ("first_name", "last_name", "email", "username"):
                            if field in data:
                                del data[field]
                        data["id"] = id_
                        update_action_payload.append(data)
                    else:
                        create_action_payload.append(data)
                else:
                    raise ActionException("Error in import.")

            if create_action_payload:
                self.execute_other_action(UserCreate, create_action_payload)
            if update_action_payload:
                self.execute_other_action(UserUpdate, update_action_payload)
        return {}

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                store_id = instance["id"]
                self.datastore.write_action_worker(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Delete,
                                fqid=fqid_from_collection_and_id(
                                    "action_worker", store_id
                                ),
                            )
                        ],
                        user_id=self.user_id,
                        locked_fields={},
                    )
                )

        return on_success
