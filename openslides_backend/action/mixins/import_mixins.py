import csv
from collections import defaultdict
from enum import Enum
from time import mktime, strptime, time
from typing import Any, Callable, Dict, List, Optional, TypedDict

from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator, Or
from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.services import DatastoreService
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action
from ..util.typing import ActionData, ActionResultElement

TRUE_VALUES = ("1", "true", "yes", "t")
FALSE_VALUES = ("0", "false", "no", "f")


class ImportState(str, Enum):
    ERROR = "error"
    NEW = "new"
    WARNING = "warning"
    DONE = "done"
    GENERATED = "generated"


class ImportMixin(Action):
    """
    Mixin for import actions. It works together with the json_upload.
    """

    import_name: str

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        self.error_store_ids: List[int] = []
        return action_data

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        store_id = instance["id"]
        worker = self.datastore.get(
            fqid_from_collection_and_id("action_worker", store_id),
            ["result", "state"],
            lock_result=False,
        )
        if (worker.get("result") or {}).get("import") != self.import_name:
            raise ActionException(
                f"Wrong id doesn't point on {self.import_name} import data."
            )
        if worker.get("state") == ImportState.ERROR:
            raise ActionException("Error in import.")
        self.result = worker["result"]
        return instance

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {
            "rows": self.result.get("rows", []),
        }

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                store_id = instance["id"]
                if store_id in self.error_store_ids:
                    continue
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


class StatisticEntry(TypedDict):
    name: str
    value: int


class JsonUploadMixin(Action):
    headers: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    statistics: List[StatisticEntry]
    state: ImportState

    def set_state(self, number_errors: int, number_warnings: int) -> None:
        if number_errors > 0:
            self.state = ImportState.ERROR
        elif number_warnings > 0:
            self.state = ImportState.WARNING
        else:
            self.state = ImportState.DONE

    def store_rows_in_the_action_worker(self, import_name: str) -> None:
        self.new_store_id = self.datastore.reserve_id(collection="action_worker")
        fqid = fqid_from_collection_and_id("action_worker", self.new_store_id)
        time_created = int(time())
        self.datastore.write_action_worker(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=fqid,
                        fields={
                            "id": self.new_store_id,
                            "result": {"import": import_name, "rows": self.rows},
                            "created": time_created,
                            "timestamp": time_created,
                            "state": self.state,
                        },
                    )
                ],
                user_id=self.user_id,
                locked_fields={},
            )
        )

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {
            "id": self.new_store_id,
            "headers": self.headers,
            "rows": self.rows,
            "statistics": self.statistics,
            "state": self.state,
        }

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        # filter extra, not needed fields before validate and parse some fields
        property_to_type = {
            header["property"]: (header["type"], header.get("is_list", False))
            for header in self.headers
        }
        for entry in list(instance.get("data", [])):
            for field in dict(entry):
                if field not in property_to_type:
                    del entry[field]
                else:
                    type_, is_list = property_to_type[field]
                    if type_ == "integer":
                        try:
                            entry[field] = int(entry[field])
                        except ValueError:
                            raise ActionException(
                                f"Could not parse {entry[field]} expect integer"
                            )
                    elif type_ == "boolean":
                        if entry[field].lower() in TRUE_VALUES:
                            entry[field] = True
                        elif entry[field].lower() in FALSE_VALUES:
                            entry[field] = False
                        else:
                            raise ActionException(
                                f"Could not parse {entry[field]} expect boolean"
                            )
                    elif type_ == "date":
                        try:
                            entry[field] = int(
                                mktime(strptime(entry[field], "%Y-%m-%d"))
                            )
                        except Exception:
                            raise ActionException(
                                f"Could not parse {entry[field]} except date"
                            )
                    elif type_ == "string" and is_list:
                        try:
                            entry[field] = [
                                item.strip()
                                for item in list(csv.reader([entry[field]]))[0]
                            ]
                        except Exception:
                            raise ActionException(
                                f"Could not parse {entry[field]} as string[]"
                            )

        super().validate_instance(instance)


class ResultType(Enum):
    """Used by Lookup to differ the possible results in check_duplicate."""

    FOUND_ID = 1
    FOUND_MORE_IDS = 2
    NOT_FOUND = 3


class Lookup:
    def __init__(
        self,
        datastore: DatastoreService,
        collection: str,
        names: List[str],
        field: str = "name",
    ) -> None:
        self.name_to_ids: Dict[str, List[int]] = defaultdict(list)
        if names:
            for entry in datastore.filter(
                collection,
                Or(*[FilterOperator(field, "=", name) for name in names]),
                ["id", field],
                lock_result=False,
            ).values():
                self.name_to_ids[entry[field]].append(entry["id"])

    def check_duplicate(self, name: str) -> ResultType:
        if not self.name_to_ids[name]:
            return ResultType.NOT_FOUND
        elif len(self.name_to_ids[name]) > 1:
            return ResultType.FOUND_MORE_IDS
        else:
            return ResultType.FOUND_ID

    def get_id_by_name(self, name: str) -> Optional[int]:
        if len(self.name_to_ids[name]) == 1:
            return self.name_to_ids[name][0]
        return None
