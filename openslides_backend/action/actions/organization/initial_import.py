from typing import Any, Dict, Iterable, Optional, Tuple

from ....models.checker import Checker, CheckException
from ....models.models import Organization
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement, ActionResults


@register_action("organization.initial_import")
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
        action_data = self.get_updated_instances(action_data)
        instance = next(iter(action_data))
        self.validate_instance(instance)
        try:
            self.check_permissions(instance)
        except MissingPermission as e:
            msg = f"You are not allowed to perform action {self.name}."
            e.message = msg + " " + e.message
            raise e
        instance = self.base_update_instance(instance)
        self.write_requests.extend(self.create_write_requests(instance))
        final_write_request = self.process_write_requests()
        result = [self.create_action_result_element(instance)]
        return (final_write_request, result)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance["data"]

        # check datavalidation
        checker = Checker(data=data, mode="all")
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        return instance

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

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"id": 1}

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        return
