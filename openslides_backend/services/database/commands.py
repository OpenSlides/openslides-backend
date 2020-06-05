from typing import Any, Dict, List, Optional

from openslides_backend.services.database.adapter.interface import GetManyRequest
from openslides_backend.shared.filters import Filter as FilterInterface
from openslides_backend.shared.patterns import Collection, FullQualifiedId


class Command:
    """
    Command is the base class for commands used by the Engine interface.
    """

    @property
    def data(self) -> Any:
        pass

    def __eq__(self, other: Any) -> bool:
        return self.data == other.data


class Get(Command):
    """
    Get command
    """

    def __init__(
        self,
        fqid: FullQualifiedId,
        mappedFields: Optional[List[str]],
        position: int = None,
        get_deleted_models: int = None,
    ):
        self.fqid = fqid
        self.mappedFields = mappedFields
        self.position = position
        self.get_deleted_models = get_deleted_models

    @property
    def data(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result["fqid"] = str(self.fqid)
        result["mapped_fields"] = self.mappedFields
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
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ):
        self.get_many_requests = get_many_requests
        self.mapped_fields = mapped_fields
        self.position = position
        self.get_deleted_models = get_deleted_models

    @property
    def data(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        requests = list(map(lambda x: x.to_dict(), self.get_many_requests))
        result["requests"] = requests
        if self.mapped_fields is not None:
            result["mapped_fields"] = self.mapped_fields
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
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ):
        self.collection = collection
        self.mapped_fields = mapped_fields
        self.get_deleted_models = get_deleted_models

    @property
    def data(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result["collection"] = str(self.collection)
        result["mapped_fields"] = self.mapped_fields
        if self.get_deleted_models is not None:
            result["get_deleted_models"] = self.get_deleted_models
        return result


class Exists(Command):
    """
    Exists command
    """

    def __init__(self, collection: Collection, filter: FilterInterface):
        self.collection = collection
        self.filter = filter

    @property
    def data(self) -> Dict[str, Any]:
        return {"collection": str(self.collection), "filter": self.filter.to_dict()}


class Count(Command):
    """
    Count command
    """

    def __init__(self, collection: Collection, filter: FilterInterface):
        self.collection = collection
        self.filter = filter

    @property
    def data(self) -> Dict[str, Any]:
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
    ):
        self.collection = collection
        self.filter = filter
        self.field = field
        self.type = type

    @property
    def data(self) -> Dict[str, Any]:
        result = {
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
    ):
        self.collection = collection
        self.filter = filter
        self.field = field
        self.type = type

    @property
    def data(self) -> Dict[str, Any]:
        result = {
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

    def __init__(self, collection: Collection, filter: FilterInterface):
        self.collection = collection
        self.filter = filter

    @property
    def data(self) -> Dict[str, Any]:
        return {"collection": str(self.collection), "filter": self.filter.to_dict()}
