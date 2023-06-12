import csv
from enum import Enum
from time import mktime, strptime, time
from typing import Any, Callable, Dict, List, Optional, Set, TypedDict

from ...services.datastore.commands import GetManyRequest
from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator, Or
from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.services import DatastoreService
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ..util.typing import ActionData, ActionResultElement
from .singular_action_mixin import SingularActionMixin

TRUE_VALUES = ("1", "true", "yes", "y", "t")
FALSE_VALUES = ("0", "false", "no", "n", "f")


class ImportState(str, Enum):
    NONE = "none"
    WARNING = "warning"
    NEW = "new"
    DONE = "done"
    GENERATED = "generated"
    REMOVE = "remove"
    ERROR = "error"


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
        mapped_fields: List[str] = [],
    ) -> None:
        self.datastore = datastore
        self.collection = collection
        self.field = field
        self.name_to_ids: Dict[str, List[Dict[str, Any]]] = {name: [] for name in names}
        self.id_to_name: Dict[int, str] = {}
        if "id" not in mapped_fields:
            mapped_fields.append("id")
        if field not in mapped_fields:
            mapped_fields.append(field)
        if names:
            for entry in datastore.filter(
                collection,
                Or(*[FilterOperator(field, "=", name) for name in names]),
                mapped_fields,
                lock_result=False,
            ).values():
                self.name_to_ids[entry[field]].append(entry)
                self.id_to_name[entry["id"]] = entry[field]

    def check_duplicate(self, name: str) -> ResultType:
        if not self.name_to_ids.get(name):
            return ResultType.NOT_FOUND
        elif len(self.name_to_ids[name]) > 1:
            return ResultType.FOUND_MORE_IDS
        else:
            return ResultType.FOUND_ID

    def get_id_by_name(self, name: str) -> Optional[int]:
        if len(self.name_to_ids[name]) == 1:
            return self.name_to_ids[name][0]["id"]
        return None

    def get_name_by_id(self, id_: int) -> Optional[str]:
        if name := self.id_to_name.get(id_):
            return name
        return None

    def read_missing_ids(self, ids: List[int]) -> None:
        result = self.datastore.get_many(
            [GetManyRequest(self.collection, ids, [self.field])],
            lock_result=False,
            use_changed_models=False,
        )
        self.id_to_name.update(
            {
                key: value.get(self.field, "")
                for key, value in result[self.collection].items()
            }
        )


class ImportMixin(SingularActionMixin):
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


class JsonUploadMixin(SingularActionMixin):
    headers: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    statistics: List[StatisticEntry]
    import_state: ImportState

    """
    # next fields have to be set in subclass, see committee/json_upload.py.
    # Implements helpful handling for list fields like admins, organization_tags
    """
    import_object_lookup: Lookup  # to be defined and initiated in subclass
    import_object_name: str  # to be set in subclass for each entry
    payload_db_field: Dict[str, str]  # mapping payload fieldname to db-id-field

    def set_state(self, number_errors: int, number_warnings: int) -> None:
        """
        To remove, but is used in some backend imports
        """
        if number_errors > 0:
            self.import_state = ImportState.ERROR
        elif number_warnings > 0:
            self.import_state = ImportState.WARNING
        else:
            self.import_state = ImportState.DONE

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
                            "state": self.import_state,
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
            "state": self.import_state,
        }

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        # filter extra, not needed fields before validate and parse some fields
        property_to_type = {
            header["property"]: (
                header["type"],
                header.get("is_object"),
                header.get("is_list", False),
            )
            for header in self.headers
        }
        for entry in list(instance.get("data", [])):
            for field in dict(entry):
                if field not in property_to_type:
                    del entry[field]
                else:
                    type_, is_object, is_list = property_to_type[field]
                    if type_ == "string" and is_list:
                        try:
                            entry[field] = [
                                item.strip()
                                for item in list(csv.reader([entry[field]]))[0]
                            ]
                        except Exception:
                            pass
                    elif type_ == "string":
                        continue
                    elif type_ == "integer":
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
                            pass
                    else:
                        raise ActionException(
                            f"Unknown type in conversion: type:{type_} is_object:{str(is_object)} is_list:{str(is_list)}"
                        )
        super().validate_instance(instance)

    def check_list_field(
        self,
        field: str,
        entry: Dict[str, Any],
        lookup: Lookup,
        messages: List[str],
        not_found_state: ImportState = ImportState.ERROR,
    ) -> None:
        if field in entry:
            # check for parse error
            if isinstance(entry[field], str):
                entry[field] = [entry[field]]

            # found_list and remove_duplicate_list are used to cut duplicates
            found_for_duplicate_list: List[str] = []
            remove_duplicate_list: List[str] = []
            remove_list: List[str] = []
            not_unique_list: List[str] = []
            missing_list: List[str] = []
            db_set_names: Set[str] = set()

            # removed objects
            if db_field := self.payload_db_field.get(field):
                db_list_ids = (
                    self.import_object_lookup.name_to_ids[self.import_object_name][
                        0
                    ].get(db_field, [])
                    or []
                )
                db_set_names = set([lookup.id_to_name[id_] for id_ in db_list_ids])
                new_list_names = set(entry[field])
                remove_list = list(db_set_names - new_list_names)
                remove_list.sort()  # necessary for test

            for i, name in enumerate(entry[field]):
                if name in found_for_duplicate_list:
                    remove_duplicate_list.append(name)
                    entry[field][i] = {"value": name, "info": ImportState.WARNING}
                    continue

                found_for_duplicate_list.append(name)
                check_duplicate = lookup.check_duplicate(name)
                if check_duplicate == ResultType.FOUND_ID:
                    id_ = lookup.get_id_by_name(name)
                    entry[field][i] = {
                        "value": name,
                        # import states signalize a new relation, not the creation of an element
                        "info": ImportState.DONE
                        if name in db_set_names
                        else ImportState.NEW,
                    }
                    if id_:
                        entry[field][i]["id"] = id_
                elif check_duplicate == ResultType.FOUND_MORE_IDS:
                    entry[field][i] = {"value": name, "info": ImportState.WARNING}
                    not_unique_list.append(name)
                else:
                    entry[field][i] = {"value": name, "info": not_found_state}
                    if not_found_state != ImportState.NEW:
                        missing_list.append(name)

            self.append_message_for_list_fields(
                not_unique_list,
                "Not identifiable {field}, because name not unique: [{incorrects}]",
                field,
                messages,
            )
            self.append_message_for_list_fields(
                missing_list, "Missing {field}: [{incorrects}]", field, messages
            )
            self.append_message_for_list_fields(
                remove_list, "Removed {field}: [{incorrects}]", field, messages
            )
            self.append_message_for_list_fields(
                remove_duplicate_list,
                "Removed duplicated {field}: [{incorrects}]",
                field,
                messages,
            )

    def append_message_for_list_fields(
        self, list_names: List[str], template: str, field: str, messages: List[str]
    ) -> None:
        if list_names:
            list_str = ", ".join(list_names)
            object = field.replace("_", " ")[:-1] + "(s)"
            messages.append(template.format(field=object, incorrects=list_str))
