from typing import Any, Dict, List, Optional, Set, Union

import simplejson as json
from mypy_extensions import TypedDict

from ...shared.filters import Filter as FilterInterface
from ...shared.filters import FilterData
from ...shared.interfaces.event import Event
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from .deleted_models_behaviour import DeletedModelsBehaviour

GetManyRequestData = TypedDict(
    "GetManyRequestData",
    {"collection": str, "ids": List[int], "mapped_fields": List[str]},
    total=False,
)


class GetManyRequest:
    """
    Encapsulates a single GetManyRequest to be used for get_many requests to the
    datastore.
    """

    mapped_fields: Optional[Set[str]]

    def __init__(
        self,
        collection: Collection,
        ids: List[int],
        mapped_fields: Union[Set[str], List[str]] = None,
    ) -> None:
        self.collection = collection
        self.ids = ids
        if isinstance(mapped_fields, list):
            self.mapped_fields = set(mapped_fields)
        else:
            self.mapped_fields = mapped_fields

    def to_dict(self) -> GetManyRequestData:
        result: GetManyRequestData = {
            "collection": str(self.collection),
            "ids": self.ids,
        }
        if self.mapped_fields is not None:
            result["mapped_fields"] = list(self.mapped_fields)
        return result


CommandData = Dict[
    str, Union[str, int, List[str], List[GetManyRequestData], FilterData]
]


StringifiedWriteRequest = TypedDict(
    "StringifiedWriteRequest",
    {
        "events": List[Event],
        "information": Dict[str, List[str]],
        "user_id": int,
        "locked_fields": Dict[str, int],
    },
)


StringifiedWriteRequests = List[StringifiedWriteRequest]


class Command:
    """
    Command is the base class for commands used by the Engine interface.

    The property 'name' returns by default the name of the class converted to snake case.
    """

    @property
    def name(self) -> str:
        name = type(self).__name__
        return "".join(
            ["_" + char.lower() if char.isupper() else char for char in name]
        ).lstrip("_")

    @property
    def data(self) -> Optional[str]:
        return json.dumps(self.get_raw_data())

    def get_raw_data(self) -> CommandData:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Command):
            return NotImplemented
        return self.data == other.data


class Get(Command):
    """
    Get command
    """

    def __init__(
        self,
        fqid: FullQualifiedId,
        mapped_fields: Set[str] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = None,
    ) -> None:
        self.fqid = fqid
        self.mapped_fields = mapped_fields
        self.position = position
        self.get_deleted_models = get_deleted_models

    def get_raw_data(self) -> CommandData:
        result: CommandData = {}
        result["fqid"] = str(self.fqid)
        if self.mapped_fields is not None:
            result["mapped_fields"] = list(self.mapped_fields)
        if self.position is not None:
            result["position"] = self.position
        if self.get_deleted_models is not None:
            result["get_deleted_models"] = self.get_deleted_models
        return result


class GetMany(Command):
    """
    GetMany command
    """

    def __init__(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: Set[str] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = None,
    ) -> None:
        self.get_many_requests = get_many_requests
        self.mapped_fields = mapped_fields
        self.position = position
        self.get_deleted_models = get_deleted_models

    def get_raw_data(self) -> CommandData:
        result: CommandData = {}
        requests = list(
            map(
                lambda get_many_request: get_many_request.to_dict(),
                self.get_many_requests,
            )
        )
        result["requests"] = requests
        if self.mapped_fields is not None:
            result["mapped_fields"] = list(self.mapped_fields)
        if self.position is not None:
            result["position"] = self.position
        if self.get_deleted_models is not None:
            result["get_deleted_models"] = self.get_deleted_models
        return result


class GetAll(Command):
    """
    GetAll command
    """

    def __init__(
        self,
        collection: Collection,
        mapped_fields: Set[str] = None,
        get_deleted_models: DeletedModelsBehaviour = None,
    ) -> None:
        self.collection = collection
        self.mapped_fields = mapped_fields
        self.get_deleted_models = get_deleted_models

    def get_raw_data(self) -> Dict[str, Any]:
        result: CommandData = {}
        result["collection"] = str(self.collection)
        if self.mapped_fields is not None:
            result["mapped_fields"] = list(self.mapped_fields)
        if self.get_deleted_models is not None:
            result["get_deleted_models"] = self.get_deleted_models
        return result


class Exists(Command):
    """
    Exists command
    """

    def __init__(self, collection: Collection, filter: FilterInterface) -> None:
        self.collection = collection
        self.filter = filter

    def get_raw_data(self) -> CommandData:
        return {"collection": str(self.collection), "filter": self.filter.to_dict()}


class Count(Command):
    """
    Count command
    """

    def __init__(self, collection: Collection, filter: FilterInterface) -> None:
        self.collection = collection
        self.filter = filter

    def get_raw_data(self) -> CommandData:
        return {"collection": str(self.collection), "filter": self.filter.to_dict()}


class Min(Command):
    """
    Min command
    """

    def __init__(
        self,
        collection: Collection,
        filter: FilterInterface,
        field: str,
        type: str = None,
    ) -> None:
        self.collection = collection
        self.filter = filter
        self.field = field
        self.type = type

    def get_raw_data(self) -> CommandData:
        result: CommandData = {
            "collection": str(self.collection),
            "filter": self.filter.to_dict(),
            "field": self.field,
        }
        if self.type is not None:
            result["type"] = self.type
        return result


class Max(Command):
    """
    Max command
    """

    def __init__(
        self,
        collection: Collection,
        filter: FilterInterface,
        field: str,
        type: str = None,
    ) -> None:
        self.collection = collection
        self.filter = filter
        self.field = field
        self.type = type

    def get_raw_data(self) -> CommandData:
        result: CommandData = {
            "collection": str(self.collection),
            "filter": self.filter.to_dict(),
            "field": self.field,
        }
        if self.type is not None:
            result["type"] = self.type
        return result


class Filter(Command):
    """
    Filter command
    """

    def __init__(
        self,
        collection: Collection,
        filter: FilterInterface,
        mapped_fields: Set[str] = None,
    ) -> None:
        self.collection = collection
        self.filter = filter
        self.mapped_fields = mapped_fields

    def get_raw_data(self) -> CommandData:
        result: CommandData = {
            "collection": str(self.collection),
            "filter": self.filter.to_dict(),
        }
        if self.mapped_fields is not None:
            result["mapped_fields"] = list(self.mapped_fields)
        return result


class ReserveIds(Command):
    """
    Reserve ids command
    """

    def __init__(self, collection: Collection, amount: int) -> None:
        self.collection = collection
        self.amount = amount

    def get_raw_data(self) -> CommandData:
        return {"collection": str(self.collection), "amount": self.amount}


class Write(Command):
    """
    Write command
    """

    def __init__(self, write_requests: List[WriteRequest]) -> None:
        self.write_requests = write_requests

    @property
    def data(self) -> str:
        stringified_write_requests: StringifiedWriteRequests = []
        for write_request in self.write_requests:
            information = {}
            for fqid, value in write_request.information.items():
                information[str(fqid)] = value
            stringified_write_requests.append(
                {
                    "events": write_request.events,
                    "information": information,
                    "user_id": write_request.user_id,
                    "locked_fields": write_request.locked_fields,
                }
            )

        class WriteRequestJSONEncoder(json.JSONEncoder):
            def default(self, o):  # type: ignore
                if isinstance(o, FullQualifiedId):
                    return str(o)
                return super().default(o)

        return json.dumps(stringified_write_requests, cls=WriteRequestJSONEncoder)


class TruncateDb(Command):
    """
    TruncateDb command. Does not need data.
    """

    @property
    def data(self) -> None:
        pass
