import copy
import csv
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from time import mktime, strptime, time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union, cast

from typing_extensions import NotRequired

from ...models.models import ImportPreview
from ...shared.exceptions import ActionException
from ...shared.filters import And, Filter, FilterOperator, Or
from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.services import DatastoreService
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ...shared.schema import required_id_schema
from ..util.default_schema import DefaultSchema
from ..util.typing import ActionData, ActionResultElement
from .singular_action_mixin import SingularActionMixin

TRUE_VALUES = ("1", "true", "yes", "y", "t")
FALSE_VALUES = ("0", "false", "no", "n", "f")

# A searchfield can be a string or a tuple of strings
SearchFieldType = Union[str, Tuple[str, ...]]


class ImportState(str, Enum):
    WARNING = "warning"
    NEW = "new"
    DONE = "done"
    GENERATED = "generated"
    REMOVE = "remove"
    ERROR = "error"


class ImportRow(TypedDict):
    state: ImportState
    data: Dict[str, Any]
    messages: List[str]


class ResultType(Enum):
    """Used by Lookup to differ the possible results in check_duplicate."""

    FOUND_ID = 1
    FOUND_MORE_IDS = 2
    NOT_FOUND = 3
    NOT_FOUND_ANYMORE = 4


class Lookup:
    def __init__(
        self,
        datastore: DatastoreService,
        collection: str,
        name_entries: List[Tuple[SearchFieldType, Dict[str, Any]]],
        field: SearchFieldType = "name",
        mapped_fields: Optional[List[str]] = None,
        global_and_filter: Optional[Filter] = None,
    ) -> None:
        if mapped_fields is None:
            mapped_fields = []
        self.datastore = datastore
        self.collection = collection
        self.field = field
        self.name_to_ids: Dict[SearchFieldType, List[Dict[str, Any]]] = defaultdict(
            list
        )
        for name, name_entry in name_entries:
            if name in self.name_to_ids:
                self.name_to_ids[name].append(name_entry)
            else:
                self.name_to_ids[name] = []
        self.id_to_name: Dict[int, List[SearchFieldType]] = defaultdict(list)
        or_filters: List[Filter] = []
        if "id" not in mapped_fields:
            mapped_fields.append("id")
        if type(field) is str:
            if field not in mapped_fields:
                mapped_fields.append(field)
            if name_entries:
                or_filters = [
                    FilterOperator(field, "=", name) for name, _ in name_entries
                ]
        else:
            mapped_fields.extend((f for f in field if f not in mapped_fields))
            if name_entries:
                or_filters = [
                    And(*[FilterOperator(field[i], "=", name_tpl[i]) for i in range(3)])
                    for name_tpl, _ in name_entries
                ]
        if or_filters:
            if global_and_filter:
                filter_: Filter = And(global_and_filter, Or(*or_filters))
            else:
                filter_ = Or(*or_filters)

            for entry in datastore.filter(
                collection,
                filter_,
                mapped_fields,
                lock_result=False,
            ).values():
                self.add_item(entry)

        # Add action data items not found in database to lookup dict
        for name, entry in name_entries:
            if values := self.name_to_ids[name]:
                if not values[0].get("id"):
                    values.append(entry)
            else:
                if type(self.field) is str:
                    obj = entry.get(self.field)
                    if type(obj) is dict and obj.get("id"):
                        obj["info"] = ImportState.ERROR
                values.append(entry)

    def check_duplicate(self, name: SearchFieldType) -> ResultType:
        if len(values := self.name_to_ids.get(name, [])) == 1:
            if (entry := values[0]).get("id"):
                if (
                    type(self.field) is str
                    and type(obj := entry[self.field]) is dict
                    and obj["info"] == ImportState.ERROR
                ):
                    return ResultType.NOT_FOUND_ANYMORE
                return ResultType.FOUND_ID
            else:
                return ResultType.NOT_FOUND
        elif len(values) > 1:
            return ResultType.FOUND_MORE_IDS
        raise ActionException("Logical Error in Lookup Class")

    def get_field_by_name(
        self, name: SearchFieldType, fieldname: str
    ) -> Optional[Union[int, str, bool]]:
        """Gets 'fieldname' from value of name_to_ids-dict"""
        if len(self.name_to_ids.get(name, [])) == 1:
            return self.name_to_ids[name][0].get(fieldname)
        return None

    def add_item(self, entry: Dict[str, Any]) -> None:
        if type(self.field) is str:
            if type(key := entry[self.field]) is dict:
                key = key["value"]
        else:
            key = tuple(entry.get(f, "") for f in self.field)
        if id_ := entry.get("id"):
            self.id_to_name[id_].append(key)
            self.name_to_ids[key].insert(0, entry)
        else:
            self.name_to_ids[key].append(entry)


class BaseImportJsonUpload(SingularActionMixin):
    import_name: str

    @staticmethod
    def count_warnings_in_payload(
        data: Union[List[Union[Dict[str, str], List[Any]]], Dict[str, Any]]
    ) -> int:
        count = 0
        for col in data:
            if type(col) is dict:
                if col.get("info") == ImportState.WARNING:
                    count += 1
            elif type(col) is list:
                count += BaseImportJsonUpload.count_warnings_in_payload(col)
        return count

    @staticmethod
    def get_value_from_union_str_object(
        field: Optional[Union[str, Dict[str, Any]]]
    ) -> Optional[str]:
        if type(field) is dict:
            return field.get("value", "")
        elif type(field) is str:
            return field
        else:
            return None


class ImportMixin(BaseImportJsonUpload):
    """
    Mixin for import actions. It works together with the json_upload.
    """

    model = ImportPreview()
    schema = DefaultSchema(model).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )

    rows: List[ImportRow]
    result: Dict[str, List]
    import_state = ImportState.DONE

    def prefetch(self, action_data: ActionData) -> None:
        store_id = cast(List[Dict[str, Any]], action_data)[0]["id"]
        import_preview = self.datastore.get(
            fqid_from_collection_and_id("import_preview", store_id),
            ["result", "state", "name"],
            lock_result=False,
        )
        if import_preview.get("name") != self.import_name:
            raise ActionException(
                f"Wrong id doesn't point on {self.import_name} import data."
            )
        if import_preview.get("state") not in list(ImportState):
            raise ActionException(
                "Error in import: Missing valid state in stored import_preview."
            )
        if import_preview.get("state") == ImportState.ERROR:
            raise ActionException("Error in import. Data will not be imported.")
        self.result = import_preview.get("result", {})
        self.rows = self.result.get("rows", [])

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if not instance["import"]:
            return {}
        return super().base_update_instance(instance)

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"rows": self.rows, "state": self.import_state}

    def validate_with_lookup(
        self,
        row: ImportRow,
        lookup: Lookup,
        field: str = "name",
        required: bool = True,
        expected_id: Optional[int] = None,
    ) -> Optional[int]:
        entry = row["data"]
        value = self.get_value_from_union_str_object(entry.get(field))
        if not value:
            if required:
                raise ActionException(
                    f"Invalid JsonUpload data: The data from json upload must contain a valid {field} object"
                )
            else:
                return None
        check_result = lookup.check_duplicate(value)
        id_ = cast(int, lookup.get_field_by_name(value, "id"))

        error: Optional[str] = None
        if check_result == ResultType.FOUND_ID and id_ != 0:
            if required:
                if row["state"] != ImportState.DONE:
                    error = f"Error: row state expected to be '{ImportState.DONE}', but it is '{row['state']}'."
                elif "id" not in entry:
                    raise ActionException(
                        f"Invalid JsonUpload data: A data row with state '{ImportState.DONE}' must have an 'id'"
                    )
            if not error:
                expected_id = entry["id"] if required else expected_id
                if id_ != expected_id:
                    error = f"Error: {field} '{value}' found in different id ({id_} instead of {expected_id})"
        elif check_result == ResultType.FOUND_MORE_IDS:
            error = f"Error: {field} '{value}' is duplicated in import."
        elif check_result == ResultType.NOT_FOUND_ANYMORE:
            if required:
                error = f"Error: {self.import_name} {entry[field]['id']} not found anymore for updating {self.import_name} '{value}'."
            else:
                error = f"Error: {field} '{value}' not found anymore in {self.import_name} with id '{id_}'"

        if error:
            row["messages"].append(error)
            entry[field]["info"] = ImportState.ERROR
            row["state"] = ImportState.ERROR
        return id_

    def validate_field(
        self, row: ImportRow, name_map: Dict[int, str], field: str, is_list: bool = True
    ) -> bool:
        valid = False
        value = row["data"].get(field)
        if value:
            arr = value if is_list else [value]
            for obj in arr:
                if not (id := obj.get("id")):
                    continue
                if id in name_map:
                    if name_map[id] == obj["value"]:
                        valid = True
                    else:
                        obj["info"] = ImportState.WARNING
                        row["messages"].append(
                            f"Expected model '{id} {obj['value']}' changed its name to '{name_map[id]}'."
                        )
                else:
                    obj["info"] = ImportState.WARNING
                    row["messages"].append(
                        f"Model '{id} {obj['value']}' doesn't exist anymore"
                    )
        return valid

    def flatten_copied_object_fields(
        self,
        hook_method: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> List[ImportRow]:
        """The self.rows will be deepcopied, flattened and returned, without
        changes on the self.rows.
        This is necessary for using the data in the executution of actions.
        The requests response should be given with the unchanged self.rows.
        Parameter:
        hook_method:
           Method to get an entry Dict[str,Any] and return it modified
        """
        rows = copy.deepcopy(self.rows)
        for row in rows:
            entry = row["data"]
            if hook_method:
                entry = hook_method(entry)
                row["data"] = entry
            for key, value in entry.items():
                if isinstance(value, list):
                    result_list = []
                    for obj in value:
                        if isinstance(obj, dict):
                            if "id" in obj:
                                result_list.append(obj["id"])
                            else:
                                result_list.append(obj["value"])
                        else:
                            result_list.append(obj)
                    entry[key] = result_list
                elif isinstance(dvalue := entry[key], dict):
                    entry[key] = dvalue["value"]
        return rows

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                store_id = instance["id"]
                if self.import_state == ImportState.ERROR:
                    continue
                self.datastore.write_without_events(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Delete,
                                fqid=fqid_from_collection_and_id(
                                    "import_preview", store_id
                                ),
                            )
                        ],
                        user_id=self.user_id,
                        locked_fields={},
                    )
                )

        return on_success


class HeaderEntry(TypedDict):
    property: str
    type: str
    is_object: NotRequired[bool]
    is_list: NotRequired[bool]


class StatisticEntry(TypedDict):
    name: str
    value: int


class JsonUploadMixin(BaseImportJsonUpload):
    headers: List[HeaderEntry]
    rows: List[Dict[str, Any]]
    statistics: List[StatisticEntry]
    import_state: ImportState
    meeting_id: int

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().base_update_instance(instance)
        self.store_rows_in_the_import_preview(self.import_name)
        return instance

    def set_state(self, number_errors: int, number_warnings: int) -> None:
        if number_errors > 0:
            self.import_state = ImportState.ERROR
        elif number_warnings > 0:
            self.import_state = ImportState.WARNING
        else:
            self.import_state = ImportState.DONE

    def store_rows_in_the_import_preview(self, import_name: str) -> None:
        self.new_store_id = self.datastore.reserve_id(collection="import_preview")
        fqid = fqid_from_collection_and_id("import_preview", self.new_store_id)
        time_created = int(time())
        result: Dict[str, Union[List[Dict[str, Any]], int]] = {"rows": self.rows}
        if hasattr(self, "meeting_id"):
            result["meeting_id"] = self.meeting_id
        self.datastore.write_without_events(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=fqid,
                        fields={
                            "id": self.new_store_id,
                            "name": import_name,
                            "result": result,
                            "created": time_created,
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

    def add_payload_index_to_action_data(self, action_data: ActionData) -> ActionData:
        for payload_index, entry in enumerate(action_data):
            entry["payload_index"] = payload_index
        return action_data

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
                    elif type_ == "decimal":
                        entry[field] = str(Decimal("0.000000") + Decimal(entry[field]))
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
                            raise ActionException(
                                f"Invalid date format: {entry[field]} (expected YYYY-MM-DD)"
                            )
                    else:
                        raise ActionException(
                            f"Unknown type in conversion: type:{type_} is_object:{str(is_object)} is_list:{str(is_list)}"
                        )
        super().validate_instance(instance)
        if "meeting_id" in instance:
            id_ = instance["meeting_id"]
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", id_),
                ["id"],
                lock_result=False,
                raise_exception=False,
            )
            if not meeting:
                raise ActionException(
                    f"Participant import tries to use non-existent meeting {id_}"
                )

    def generate_statistics(self) -> None:
        """
        Generates the default statistics for the import preview.
        Also sets the global state accordingly.
        """
        state_to_count: Dict[ImportState, int] = defaultdict(int)
        for row in self.rows:
            state_to_count[row["state"]] += 1
            state_to_count[ImportState.WARNING] += self.count_warnings_in_payload(
                row.get("data", {}).values()
            )
            row["data"].pop("payload_index", None)

        self.statistics = [
            {"name": "total", "value": len(self.rows)},
            {"name": "created", "value": state_to_count[ImportState.NEW]},
            {"name": "updated", "value": state_to_count[ImportState.DONE]},
            {"name": "error", "value": state_to_count[ImportState.ERROR]},
            {"name": "warning", "value": state_to_count[ImportState.WARNING]},
        ]
        self.set_state(
            state_to_count[ImportState.ERROR], state_to_count[ImportState.WARNING]
        )
