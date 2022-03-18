from typing import Any, Dict, Iterable, Optional, Tuple

from datastore.shared.util import DeletedModelsBehaviour

from migrations import get_backend_migration_index

from ....models.checker import Checker, CheckException
from ....models.models import Organization
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import Collection, FullQualifiedId
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

        self.check_migration_index(instance)

        # check datavalidation
        checker = Checker(data=data, mode="all")
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        return instance

    def check_empty_datastore(self) -> None:
        filter_ = FilterOperator("id", ">=", 1)
        if self.datastore.exists(
            Collection("organization"),
            filter_,
            DeletedModelsBehaviour.ALL_MODELS,
            False,
        ):
            raise ActionException("Datastore is not empty.")

    def check_migration_index(self, instance: Dict[str, Any]) -> None:
        self.data_migration_index = instance["data"].get("_migration_index")
        self.backend_migration_index = get_backend_migration_index()
        if self.data_migration_index is None:
            raise ActionException(
                "Data must have a valid migration index in `_migration_index`."
            )
        if self.data_migration_index < 1:
            raise ActionException(
                f"Data must have a valid migration index >= 1, but has {self.data_migration_index}."
            )

        if self.backend_migration_index < self.data_migration_index:
            raise ActionException(
                f"Migration indices do not match: Data has {self.data_migration_index} and the backend has {self.backend_migration_index}"
            )

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        json_data = instance["data"]
        write_requests = []
        for collection in json_data:
            for entry in json_data[collection].values():
                fqid = FullQualifiedId(Collection(collection), entry["id"])
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
        result = {
            "data_migration_index": self.data_migration_index,
            "backend_migration_index": self.backend_migration_index,
        }
        if self.backend_migration_index > self.data_migration_index:
            result["message"] = "Data imported, but must be migrated!"
        else:
            result[
                "message"
            ] = f"Data imported, Migration Index set to {self.backend_migration_index}"
        return result
