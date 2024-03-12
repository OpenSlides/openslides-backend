from typing import Any, Union

import simplejson as json

from ...shared.filters import _FilterBase as FilterInterface
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection


class GetManyRequest:
    """
    Encapsulates a single GetManyRequest to be used for get_many requests to the
    datastore.
    """

    mapped_fields: set[str]

    def __init__(
        self,
        collection: Collection,
        ids: list[int],
        mapped_fields: set[str] | list[str] | None = None,
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


CommandData = dict[str, Union[str, int, list[str]]]


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
    def data(self) -> str | None:
        return json.dumps(self.get_raw_data())

    def get_raw_data(self) -> CommandData:
        raise NotImplementedError()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Command) and self.data == other.data


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

    def __init__(self, write_requests: list[WriteRequest]) -> None:
        self.write_requests = write_requests

    @property
    def data(self) -> str:
        class WriteRequestJSONEncoder(json.JSONEncoder):
            def default(self, o: Any) -> Any:
                if isinstance(o, WriteRequest):
                    return o.__dict__
                if isinstance(o, FilterInterface):
                    return o.to_dict()
                return super().default(o)

        return json.dumps(self.write_requests, cls=WriteRequestJSONEncoder)


class WriteWithoutEvents(Write):
    """
    WriteWithoutEvents command, same as Write, but on separate route
    """


class TruncateDb(Command):
    """
    TruncateDb command. Does not need data.
    """

    @property
    def data(self) -> None:
        pass


class GetEverything(Command):
    """
    GetEverything command. Does not need data.
    """

    def get_raw_data(self) -> CommandData:
        return {}


class DeleteHistoryInformation(Command):
    """
    DeleteHistoryInformation command. Does not need data.
    """

    def get_raw_data(self) -> CommandData:
        return {}
