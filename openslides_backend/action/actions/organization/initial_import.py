from typing import Any, Dict, Iterable, Optional, Tuple

from datastore.shared.util import DeletedModelsBehaviour

from openslides_backend.migrations import get_backend_migration_index

from ....models.checker import Checker, CheckException
from ....models.models import Organization
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import INITIAL_DATA_FILE, get_initial_data_file
from ...action import Action
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults


@register_action("organization.initial_import", action_type=ActionType.STACK_INTERNAL)
class OrganizationInitialImport(SingularActionMixin, Action):
    """
    Action to import an initial-data.json in an empty datastore.
    Should be callable from the management service.
    """

    model = Organization()
    schema = DefaultSchema(Organization()).get_default_schema(
        additional_required_fields={"data": {"type": "object"}},
        title="Import initial data.",
        description="Import an initial data json in an empty datastore.",
    )

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        """
        Simplified entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        instance = next(iter(action_data))
        self.validate_instance(instance)
        instance = self.update_instance(instance)
        self.write_requests.extend(self.create_write_requests(instance))
        result = self.create_action_result_element(instance)
        self.results.append(result)
        final_write_request = self.process_write_requests()
        return (final_write_request, self.results)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance["data"]

        self.check_empty_datastore()

        if not data:
            data = get_initial_data_file(INITIAL_DATA_FILE)
            instance["data"] = data

        # check datavalidation
        checker = Checker(data=data, mode="all", migration_mode="permissive")
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        self.data_migration_index = data["_migration_index"]

        return instance

    def check_empty_datastore(self) -> None:
        filter_ = FilterOperator("id", ">=", 1)
        if self.datastore.exists(
            "organization",
            filter_,
            DeletedModelsBehaviour.ALL_MODELS,
            False,
        ):
            raise ActionException("Datastore is not empty.")

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        json_data = instance["data"]
        write_requests = []
        for collection in json_data:
            if collection.startswith("_"):
                continue
            for entry in json_data[collection].values():
                fqid = fqid_from_collection_and_id(collection, entry["id"])
                write_requests.append(
                    self.build_write_request(
                        EventType.Create,
                        fqid,
                        "initial import",
                        entry,
                    )
                )
        return write_requests

    def process_write_requests(
        self,
    ) -> Optional[WriteRequest]:
        """
        Add Migration Index to the one and only write request
        """
        write_request = super().process_write_requests()
        if write_request:
            write_request.migration_index = self.data_migration_index
        return write_request

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        backend_migration_index = get_backend_migration_index()
        result = {
            "data_migration_index": self.data_migration_index,
            "backend_migration_index": backend_migration_index,
        }
        if backend_migration_index > self.data_migration_index:
            result["message"] = "Data imported, but must be migrated!"
            result["migration_needed"] = True
        else:
            result[
                "message"
            ] = f"Data imported, Migration Index set to {backend_migration_index}"
            result["migration_needed"] = False
        return result
