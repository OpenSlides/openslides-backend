from typing import Any, Dict, List, Sequence, Union

import simplejson as json
from simplejson.errors import JSONDecodeError  # type: ignore

from ...shared.exceptions import DatabaseException
from ...shared.filters import Filter
from ...shared.interfaces import LoggingModule, WriteRequestElement
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from . import commands
from .http_engine import HTTPEngine as Engine
from .interface import Aggregate, Count, Found, PartialModel

# TODO: Use proper typing here.
DatastoreResponse = Any


class Adapter:
    """
    Adapter to connect to readable and writeable datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: Dict[str, int]

    def __init__(self, engine: Engine, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.locked_fields = {}

    def retrieve(self, command: commands.Command) -> DatastoreResponse:
        """
        Uses engine to send data to datastore and retrieve result.

        This method also checks the payload and decodes JSON body.
        """
        content, status_code = self.engine.retrieve(command.name, command.data)
        if len(content):
            try:
                payload = json.loads(content)
            except JSONDecodeError:
                error_message = "Bad response from datastore service. Body does not contain valid JSON."
                raise DatabaseException(error_message)
        else:
            payload = None
        self.logger.debug(f"Get repsonse with status code {status_code}: {payload}")
        if status_code >= 400:
            error_message = f"Datastore service sends HTTP {status_code}."
            additional_error_message = (
                payload.get("error") if isinstance(payload, dict) else None
            )
            if additional_error_message is not None:
                error_message = " ".join((error_message, str(additional_error_message)))
            raise DatabaseException(error_message)
        return payload

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
        lock_result: bool = False,
    ) -> PartialModel:
        if lock_result and mapped_fields is not None:
            mapped_fields.append("meta_position")
        command = commands.Get(
            fqid=fqid,
            mappedFields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        if lock_result:
            instance_position = response.get("meta_position")
            if instance_position is None:
                raise DatabaseException(
                    "Response from datastore does not contain field 'meta_position' but this is required."
                )
            self.update_locked_fields(fqid, instance_position)
        return response

    def get_many(
        self,
        get_many_requests: List[commands.GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
        lock_result: bool = False,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        if mapped_fields is not None:
            raise NotImplementedError(
                "The keyword 'mapped_fields' is not supported. Please use mapped_fields inside the GetManyRequest."
            )
        if lock_result:
            for get_many_request in get_many_requests:
                if get_many_request.mapped_fields is not None:
                    get_many_request.mapped_fields.append("meta_position")
        command = commands.GetMany(
            get_many_requests=get_many_requests,
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET_MANY request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        result = {}
        for collection_str in response.keys():
            inner_result = {}
            collection = Collection(collection_str)
            for id_str, value in response[collection_str].items():
                instance_id = int(id_str)
                if lock_result:
                    instance_position = value.get("meta_position")
                    if instance_position is None:
                        raise DatabaseException(
                            "Response from datastore does not contain field 'meta_position' but this is required."
                        )
                    fqid = FullQualifiedId(collection, instance_id)
                    self.update_locked_fields(fqid, instance_position)
                inner_result[instance_id] = value
            result[collection] = inner_result
        return result

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
        lock_result: bool = False,
    ) -> List[PartialModel]:
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        if lock_result and mapped_fields is not None:
            mapped_fields.extend(("id", "meta_position"))
        command = commands.GetAll(
            collection=collection,
            mapped_fields=mapped_fields,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET_ALL request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        if lock_result:
            for item in response:
                instance_id = item.get("id")
                instance_position = item.get("meta_position")
                if instance_id is None or instance_position is None:
                    raise DatabaseException(
                        "Response from datastore does not contain fields 'id' and 'meta_position' but they are both required."
                    )
                fqid = FullQualifiedId(collection=collection, id=instance_id)
                self.update_locked_fields(fqid, instance_position)
        return response

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
        lock_result: bool = False,
    ) -> List[PartialModel]:
        if meeting_id is not None:
            raise NotImplementedError("The keyword 'meeting_id' is not supported yet.")
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        if lock_result and mapped_fields is not None:
            mapped_fields.extend(("id", "meta_position"))
        command = commands.Filter(
            collection=collection, filter=filter, mapped_fields=mapped_fields
        )
        self.logger.debug(
            f"Start FILTER request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        if lock_result:
            for item in response:
                instance_id = item.get("id")
                instance_position = item.get("meta_position")
                if instance_id is None or instance_position is None:
                    raise DatabaseException(
                        "Response from datastore does not contain fields 'id' and 'meta_position' but they are both required."
                    )
                fqid = FullQualifiedId(collection=collection, id=instance_id)
                self.update_locked_fields(fqid, instance_position)
        return response

    def exists(
        self, collection: Collection, filter: Filter, lock_result: bool = False,
    ) -> Found:
        command = commands.Exists(collection=collection, filter=filter)
        self.logger.debug(
            f"Start EXISTS request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        if lock_result:
            position = response.get("position")
            if position is None:
                raise DatabaseException("Invalid response from datastore.")
            raise NotImplementedError("Locking is not implemented")
        return {"exists": response["exists"]}

    def count(
        self, collection: Collection, filter: Filter, lock_result: bool = False,
    ) -> Count:
        command = commands.Count(collection=collection, filter=filter)
        self.logger.debug(
            f"Start COUNT request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        if lock_result:
            raise NotImplementedError("Locking is not implemented")
        return {"count": response["count"]}

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does not reflect the position of the fetched objects.
        command = commands.Min(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MIN request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        return response

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does not reflect the position of the fetched objects.
        command = commands.Max(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MAX request to datastore with the following data: {command.data}"
        )
        response = self.retrieve(command)
        return response

    def update_locked_fields(
        self, key: Union[FullQualifiedId, FullQualifiedField], position: int,
    ) -> None:
        """
        Updates the locked_fields map by adding the new value for the given FQId or
        FQField. If there is an existing value we take the smaller one.
        """
        current_position = self.locked_fields.get(str(key))
        if current_position is None:
            new_position = position
        else:
            new_position = min(position, current_position)
        self.locked_fields[str(key)] = new_position

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        command = commands.ReserveIds(collection=collection, amount=amount)
        self.logger.debug(
            f"Start RESERVE_IDS request to datastore with the following data: "
            f"Collection: {collection}, Amount: {amount}"
        )
        response = self.retrieve(command)
        return response.get("ids")

    def reserve_id(self, collection: Collection) -> int:
        return self.reserve_ids(collection=collection, amount=1)[0]

    def write(self, write_requests: Sequence[WriteRequestElement]) -> None:
        # TODO: Support multiple write_requests
        if len(write_requests) != 1:
            raise RuntimeError("Multiple or None write_requests not supported.")
        command = commands.Write(
            write_request=write_requests[0], locked_fields=self.locked_fields
        )
        self.logger.debug(
            f"Start WRITE request to datastore with the following data: "
            f"Write request: {write_requests[0]}"
        )
        self.retrieve(command)
