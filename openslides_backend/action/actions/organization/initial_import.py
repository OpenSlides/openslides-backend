from collections.abc import Iterable
from typing import Any

from ....i18n.translator import Translator
from ....i18n.translator import translate as _
from ....models.base import json_dict_to_non_json_data_types
from ....models.checker import Checker, CheckException
from ....models.models import Organization
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import Event, EventType
from ....shared.interfaces.write_request import (
    WriteRequest,
    WriteRequestWithMigrationIndex,
)
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
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        """
        Simplified entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        instance = next(iter(action_data))
        self.validate_instance(instance)
        instance = self.update_instance(instance)
        self.events.extend(self.create_events(instance))
        result = self.create_action_result_element(instance)
        self.results.append(result)
        write_request = self.build_write_request()
        return (write_request, self.results)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        data = instance["data"]

        self.check_empty_datastore()

        if not data:
            data = get_initial_data_file(INITIAL_DATA_FILE)
            instance["data"] = data
        json_dict_to_non_json_data_types(data)
        # check datavalidation
        checker = Checker(data=data, mode="all", migration_mode="permissive")
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))

        self.translate_organization_and_theme(data)
        self.data_migration_index = data["_migration_index"]

        return instance

    def check_empty_datastore(self) -> None:
        filter_ = FilterOperator("id", ">=", 1)
        if self.datastore.exists(
            "organization",
            filter_,
            False,
        ):
            raise ActionException("Datastore is not empty.")

    def translate_organization_and_theme(self, data: dict[str, Any]) -> None:
        organization = data["organization"]["1"]
        Translator.set_translation_language(organization["default_language"])
        translation_fields = (
            "legal_notice",
            "login_text",
            "users_email_subject",
            "users_email_body",
        )
        for field in translation_fields:
            if organization.get(field):
                organization[field] = _(organization[field])
        if data.get("theme"):
            for entry in data["theme"].values():
                if entry.get("name"):
                    entry["name"] = _(entry["name"])

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        json_data = instance["data"]
        events = []
        for collection in json_data:
            if collection.startswith("_"):
                continue
            for entry in json_data[collection].values():
                fqid = fqid_from_collection_and_id(collection, entry["id"])
                events.append(
                    self.build_event(
                        EventType.Create,
                        fqid,
                        entry,
                    )
                )
        return events

    def build_write_request(
        self,
    ) -> WriteRequest | None:
        """
        Add Migration Index to the one and only write request
        """
        write_request = self._build_write_request(WriteRequestWithMigrationIndex([]))
        if write_request:
            write_request.migration_index = self.data_migration_index
        return write_request

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        backend_migration_index = 1
        # TODO set to fixed value because of lacking migrations
        # needs to be readded in some shape or form
        # backend_migration_index = get_backend_migration_index()
        result = {
            "data_migration_index": self.data_migration_index,
            "backend_migration_index": backend_migration_index,
        }
        if backend_migration_index > self.data_migration_index:
            result["message"] = "Data imported, but must be migrated!"
            result["migration_needed"] = True
        else:
            result["message"] = (
                f"Data imported, Migration Index set to {backend_migration_index}"
            )
            result["migration_needed"] = False
        return result
