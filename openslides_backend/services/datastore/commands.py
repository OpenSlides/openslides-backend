from typing import Dict, List, Optional, Set, TypedDict, Union

import simplejson as json

from ...shared.filters import FilterBase as FilterInterface
from ...shared.interfaces.collection_field_lock import CollectionFieldLock
from ...shared.interfaces.event import Event
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId


class GetManyRequest:
    """
    Encapsulates a single GetManyRequest to be used for get_many requests to the
    datastore.
    """

    mapped_fields: Set[str]

    def __init__(
        self,
        collection: Collection,
        ids: List[int],
        mapped_fields: Optional[Union[Set[str], List[str]]] = None,
    ) -> None:
        self.collection = collection
        self.ids = ids
        if isinstance(mapped_fields, list):
            self.mapped_fields = set(mapped_fields)
        else:
            self.mapped_fields = mapped_fields or set()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, GetManyRequest)
            and self.collection == other.collection
            and self.ids == other.ids
            and self.mapped_fields == other.mapped_fields
        )

    def __repr__(self) -> str:
        return str(
            {
                "collection": self.collection,
                "ids": self.ids,
                "mapped_fields": list(self.mapped_fields),
            }
        )


CommandData = Dict[str, Union[str, int, List[str]]]


StringifiedWriteRequest = TypedDict(
    "StringifiedWriteRequest",
    {
        "events": List[Event],
        "information": Dict[str, List[str]],
        "user_id": int,
        "locked_fields": Dict[str, CollectionFieldLock],
        "migration_index": Optional[int],
    },
    total=False,
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
        raise NotImplementedError()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Command):
            return NotImplemented
        return self.data == other.data


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
            stringified_write_request: StringifiedWriteRequest = {
                "events": write_request.events,
                "information": information,
                "user_id": write_request.user_id,
                "locked_fields": write_request.locked_fields,
            }
            if write_request.migration_index:
                stringified_write_request[
                    "migration_index"
                ] = write_request.migration_index
            stringified_write_requests.append(stringified_write_request)

        class WriteRequestJSONEncoder(json.JSONEncoder):
            def default(self, o):  # type: ignore
                if isinstance(o, FullQualifiedId):
                    return str(o)
                if isinstance(o, FilterInterface):
                    return o.to_dict()
                return super().default(o)

        return json.dumps(stringified_write_requests, cls=WriteRequestJSONEncoder)


class TruncateDb(Command):
    """
    TruncateDb command. Does not need data.
    """

    @property
    def data(self) -> None:
        pass
