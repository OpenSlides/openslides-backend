from typing import Dict, List, Sequence, Union

from ...shared.filters import Filter
from ...shared.interfaces import LoggingModule, WriteRequestElement
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from . import commands
from .http_engine import HTTPEngine as Engine
from .interface import Aggregate, Count, Found, PartialModel


class Adapter:
    """
    Adapter to connect to readable and writeable datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    position: Dict[str, int]

    def __init__(self, engine: Engine, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.position = {}  # TODO: Rename to locked_fields

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        command = commands.Get(fqid=fqid, mappedFields=mapped_fields)
        self.logger.debug(
            f"Start GET request to datastore with the following data: {command.data}"
        )
        response = self.engine.get(command)
        position = response.get("meta_position")
        if position is not None:
            self.set_min_position(fqid, position)
        return response

    def get_many(
        self,
        get_many_requests: List[commands.GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        # TODO: Change return type and switch respective code here.
        command = commands.GetMany(
            get_many_requests=get_many_requests,
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET_MANY request to datastore with the following data: {command.data}"
        )
        response = self.engine.get_many(command)
        result = {}
        for collection_str in response.keys():
            inner_result = {}
            collection = Collection(collection_str)
            for id_str, value in response[collection_str].items():
                instance_id = int(id_str)
                position = value.get("meta_position")
                if position is not None:
                    fqid = FullQualifiedId(collection, instance_id)
                    self.set_min_position(fqid, position)
                inner_result[instance_id] = value
            result[collection] = inner_result
        return result

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        command = commands.GetAll(collection=collection, mapped_fields=mapped_fields)
        self.logger.debug(
            f"Start GET_ALL request to datastore with the following data: {command.data}"
        )
        response = self.engine.get_all(command)
        for item in response:
            position = item.get("meta_position")
            item_id = item.get("id")
            if position is not None and id is not None:
                fqid = FullQualifiedId(collection=collection, id=item_id)
                self.set_min_position(fqid, position)
        return response

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        command = commands.Filter(collection=collection, filter=filter)
        self.logger.debug(
            f"Start FILTER request to datastore with the following data: {command.data}"
        )
        response = self.engine.filter(command)
        for item in response:
            position = item.get("meta_position")
            item_id = item.get("id")
            if position is not None and id is not None:
                fqid = FullQualifiedId(collection=collection, id=item_id)
                self.set_min_position(fqid, position)
        return response

    def exists(self, collection: Collection, filter: Filter) -> Found:
        # Attention: We do not handle the position result of this request. You
        # have to do this manually.
        command = commands.Exists(collection=collection, filter=filter)
        self.logger.debug(
            f"Start EXISTS request to datastore with the following data: {command.data}"
        )
        response = self.engine.exists(command)
        return {"exists": response["exists"], "position": response["position"]}

    def count(self, collection: Collection, filter: Filter) -> Count:
        # Attention: We do not handle the position result of this request. You
        # have to do this manually.
        command = commands.Count(collection=collection, filter=filter)
        self.logger.debug(
            f"Start COUNT request to datastore with the following data: {command.data}"
        )
        response = self.engine.count(command)
        return {"count": response["count"], "position": response["position"]}

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does nit reflect the position of the fetched objects.
        command = commands.Min(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MIN request to datastore with the following data: {command.data}"
        )
        response = self.engine.min(command)
        return response

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does nit reflect the position of the fetched objects.
        command = commands.Max(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MAX request to datastore with the following data: {command.data}"
        )
        response = self.engine.max(command)
        return response

    def set_min_position(
        self, key: Union[FullQualifiedId, FullQualifiedField], position: int,
    ) -> None:
        """
        """
        # TODO: Rename this method and add docstring.
        current_position = self.position.get(str(key))
        if current_position is None:
            new_position = position
        else:
            new_position = min(position, current_position)
        self.position[str(key)] = new_position

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        command = commands.ReserveIds(collection=collection, amount=amount)
        self.logger.debug(
            f"Start RESERVE_IDS request to datastore with the following data: "
            f"Collection: {collection}, Amount: {amount}"
        )
        response = self.engine.reserve_ids(command)
        return response.get("ids")

    def reserve_id(self, collection: Collection) -> int:
        return self.reserve_ids(collection=collection, amount=1)[0]

    def write(self, write_requests: Sequence[WriteRequestElement]) -> None:
        # TODO: Support multiple write_requests
        if len(write_requests) != 1:
            raise RuntimeError("Multiple or None write_requests not supported.")
        command = commands.Write(
            write_request=write_requests[0], locked_fields=self.position
        )
        self.logger.debug(
            f"Start WRITE request to datastore with the following data: "
            f"Write request: {write_requests[0]}"
        )
        self.engine.write(command)
