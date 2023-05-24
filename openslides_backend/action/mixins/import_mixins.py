import csv
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from time import mktime, strptime, time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from typing_extensions import NotRequired, TypedDict

from ...shared.exceptions import ActionException
from ...shared.filters import And, Filter, FilterOperator, Or
from ...shared.interfaces.event import Event, EventType
from ...shared.interfaces.services import DatastoreService
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import fqid_from_collection_and_id
from ..util.typing import ActionData, ActionResultElement
from .singular_action_mixin import SingularActionMixin

TRUE_VALUES = ("1", "true", "yes", "y", "t")
FALSE_VALUES = ("0", "false", "no", "n", "f")

# A searchfield can be a string or a tuple of strings
SearchFieldType = Union[str, Tuple[str, ...]]


class ImportState(str, Enum):
    NONE = "none"
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
        for name, _ in name_entries:
            self.name_to_ids[name] = []
        self.id_to_name: Dict[int, List[SearchFieldType]] = defaultdict(list)
        or_filters: List[Filter] = []
        if "id" not in mapped_fields:
            mapped_fields.append("id")
        if type(field) == str:
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
            if values := cast(list, self.name_to_ids[name]):
                if not values[0].get("id"):
                    values.append(entry)
            else:
                if type(self.field) == str:
                    obj = entry[self.field]
                    if type(obj) == dict and obj.get("id"):
                        obj["info"] = ImportState.ERROR
                values.append(entry)

    def check_duplicate(self, name: SearchFieldType) -> ResultType:
        if len(values := self.name_to_ids.get(name, [])) == 1:
            if (entry := values[0]).get("id"):
                if (
                    type(self.field) == str
                    and type(obj := entry[self.field]) == dict
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
        if type(self.field) == str:
            if type(key := entry[self.field]) == dict:
                key = key["value"]
            self.name_to_ids[key].append(entry)
            if entry.get("id"):
                self.id_to_name[entry["id"]].append(entry[self.field])
        else:
            key = tuple(entry.get(f, "") for f in self.field)
            self.name_to_ids[key].append(entry)
            if entry.get("id"):
                self.id_to_name[entry["id"]].append(key)


class BaseImportJsonUpload(SingularActionMixin):
    @staticmethod
    def count_warnings_in_payload(
        data: Union[List[Union[Dict[str, str], List[Any]]], Dict[str, Any]]
    ) -> int:
        count = 0
        for col in data:
            if type(col) == dict:
                if col.get("info") == ImportState.WARNING:
                    count += 1
            elif type(col) == list:
                count += BaseImportJsonUpload.count_warnings_in_payload(col)
        return count

    @staticmethod
    def get_value_from_union_str_object(
        field: Optional[Union[str, Dict[str, Any]]]
    ) -> Optional[str]:
        if type(field) == dict:
            return field.get("value", "")
        elif type(field) == str:
            return field
        else:
            return None


class ImportMixin(BaseImportJsonUpload):
    """
    Mixin for import actions. It works together with the json_upload.
    """

    import_name: str
    rows: List[ImportRow] = []
    result: Dict[str, List] = {}
    import_state = ImportState.DONE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        store_id = instance["id"]
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
        return instance

    def handle_relation_updates(self, instance: Dict[str, Any]) -> Any:
        return {}

    def create_events(self, instance: Dict[str, Any]) -> Any:
        return []

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"rows": self.result.get("rows", []), "state": self.import_state}

    def flatten_object_fields(self, fields: Optional[List[str]] = None) -> None:
        """replace objects from self.rows["data"] with their values. Uses the fields, if given, otherwise all"""
        for row in self.rows:
            entry = row["data"]
            used_list = fields if fields else entry.keys()
            for field in used_list:
                if field in entry:
                    if type(dvalue := entry[field]) == dict:
                        entry[field] = dvalue["value"]

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


class StatisticEntry(TypedDict):
    name: str
    value: int


class JsonUploadMixin(BaseImportJsonUpload):
    headers: List[HeaderEntry]
    rows: List[Dict[str, Any]]
    statistics: List[StatisticEntry]
    import_state: ImportState

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

    def store_rows_in_the_import_preview(self, import_name: str) -> None:
        self.new_store_id = self.datastore.reserve_id(collection="import_preview")
        fqid = fqid_from_collection_and_id("import_preview", self.new_store_id)
        time_created = int(time())
        self.datastore.write_without_events(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Create,
                        fqid=fqid,
                        fields={
                            "id": self.new_store_id,
                            "name": import_name,
                            "result": {"rows": self.rows},
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
                            pass
                    else:
                        raise ActionException(
                            f"Unknown type in conversion: type:{type_} is_object:{str(is_object)} is_list:{str(is_list)}"
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
            self.name_to_ids[name].append(0)
            return ResultType.NOT_FOUND
        elif len(self.name_to_ids[name]) > 1:
            return ResultType.FOUND_MORE_IDS
        else:
            return ResultType.FOUND_ID

    def get_id_by_name(self, name: str) -> Optional[int]:
        if len(self.name_to_ids[name]) == 1:
            return self.name_to_ids[name][0]
        return None
