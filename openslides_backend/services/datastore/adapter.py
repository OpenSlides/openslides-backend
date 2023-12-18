from collections import defaultdict
from typing import Any, ContextManager, Dict, List, Optional, Sequence, Set, Union

import simplejson as json
from datastore.reader.core import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
    Reader,
)
from datastore.shared.di import injector
from datastore.shared.services.read_database import HistoryInformation
from datastore.shared.util import DeletedModelsBehaviour
from simplejson.errors import JSONDecodeError

from ...shared.exceptions import DatastoreException
from ...shared.filters import And, Filter, FilterOperator, filter_visitor
from ...shared.interfaces.collection_field_lock import (
    CollectionFieldLock,
    CollectionFieldLockWithFilter,
)
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import (
    COLLECTIONFIELD_PATTERN,
    Collection,
    CollectionField,
    FullQualifiedField,
    FullQualifiedId,
    collectionfield_from_collection_and_field,
    fqfield_from_fqid_and_field,
    fqid_from_collection_and_id,
)
from . import commands
from .handle_datastore_errors import handle_datastore_errors, raise_datastore_error
from .interface import BaseDatastoreService, Engine, LockResult, PartialModel

MappedFieldsPerFqid = Dict[FullQualifiedId, List[str]]


class DatastoreAdapter(BaseDatastoreService):
    """
    Adapter to connect to readable and writeable datastore.
    """

    reader: Reader

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField or CollectionField
    locked_fields: Dict[str, CollectionFieldLock]

    def __init__(self, engine: Engine, logging: LoggingModule, env: Env) -> None:
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.reader = injector.get(Reader)
        self.locked_fields = {}
        self.env = env

    def retrieve(self, command: commands.Command) -> Any:
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
                self.logger.error(error_message + f" Received: {str(content)}")
                raise DatastoreException(error_message)
        else:
            payload = None
        self.logger.debug(f"Get response with status code {status_code}: {payload}")
        if status_code >= 400:
            raise_datastore_error(
                payload,
                f"Datastore service sends HTTP {status_code}.",
                self.logger,
                self.env,
            )
        return payload

    def get_database_context(self) -> ContextManager[None]:
        return self.reader.get_database_context()

    @handle_datastore_errors
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> PartialModel:
        if lock_result and mapped_fields:
            mapped_fields.append("meta_position")
        request = GetRequest(
            fqid=str(fqid),
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET request to datastore with the following data: {request}"
        )
        response = self.reader.get(request)
        if lock_result:
            instance_position = response.get("meta_position")
            if not isinstance(instance_position, int):
                raise DatastoreException(
                    "Response from datastore contains invalid 'meta_position'."
                )
            if isinstance(lock_result, list):
                mapped_fields_set = set(lock_result)
            else:
                mapped_fields_set = set(mapped_fields)
            self.update_locked_fields_from_mapped_fields(
                fqid, instance_position, mapped_fields_set
            )
        return response

    @handle_datastore_errors
    def get_many(
        self,
        get_many_requests: List[commands.GetManyRequest],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        if lock_result:
            for get_many_request in get_many_requests:
                if get_many_request.mapped_fields:
                    get_many_request.mapped_fields.add("meta_position")

        request_parts = [
            GetManyRequestPart(
                str(gmr.collection), gmr.ids, list(gmr.mapped_fields or [])
            )
            for gmr in get_many_requests
        ]
        request = GetManyRequest(request_parts, [], position, get_deleted_models)
        self.logger.debug(
            f"Start GET_MANY request to datastore with the following data: {request}"
        )
        response = self.reader.get_many(request)
        result: Dict[Collection, Dict[int, PartialModel]] = defaultdict(dict)
        for get_many_request in get_many_requests:
            collection = get_many_request.collection
            if collection not in response:
                continue

            for instance_id in get_many_request.ids:
                if instance_id not in response[collection]:
                    continue
                value = response[collection][instance_id]
                if lock_result:
                    instance_position = value.get("meta_position")
                    if not isinstance(instance_position, int):
                        raise DatastoreException(
                            "Response from datastore contains invalid 'meta_position'."
                        )
                    fqid = fqid_from_collection_and_id(collection, instance_id)
                    self.update_locked_fields_from_mapped_fields(
                        fqid, instance_position, get_many_request.mapped_fields
                    )
                result[collection][instance_id] = value
        return result

    @handle_datastore_errors
    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]:
        mapped_fields_set = set(mapped_fields)
        if lock_result:
            mapped_fields_set.add("meta_position")
        request = GetAllRequest(
            collection=str(collection),
            mapped_fields=list(mapped_fields_set),
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET_ALL request to datastore with the following data: {request}"
        )
        response = self.reader.get_all(request)
        if lock_result and len(response) > 0:
            if not mapped_fields:
                raise DatastoreException(
                    "You cannot lock in get_all without mapped_fields"
                )
            for field in mapped_fields_set:
                # just take the first position, new positions will always be higher anyway
                instance_position = list(response.values())[0].get("meta_position")
                if not isinstance(instance_position, int):
                    raise DatastoreException(
                        "Response from datastore contains invalid 'meta_position'."
                    )
                collection_field = collectionfield_from_collection_and_field(
                    collection, field
                )
                self.update_locked_fields(collection_field, instance_position)
        return response

    @handle_datastore_errors
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]:
        full_filter = self.apply_deleted_models_behaviour_to_filter(
            filter, get_deleted_models
        )
        request = FilterRequest(
            collection=str(collection), filter=full_filter, mapped_fields=mapped_fields
        )
        self.logger.debug(
            f"Start FILTER request to datastore with the following data: {request}"
        )
        response = self.reader.filter(request)
        if lock_result:
            self.lock_collection_fields_from_filter(
                collection, filter, response.get("position")
            )
        return response["data"]

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> bool:
        return self._aggregate(
            "exists", collection, filter, get_deleted_models, lock_result
        )

    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> int:
        return self._aggregate(
            "count", collection, filter, get_deleted_models, lock_result
        )

    @handle_datastore_errors
    def _aggregate(
        self,
        route: str,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour,
        lock_result: bool,
    ) -> Any:
        full_filter = self.apply_deleted_models_behaviour_to_filter(
            filter, get_deleted_models
        )
        request = AggregateRequest(collection=str(collection), filter=full_filter)
        self.logger.debug(
            f"Start {route.upper()} request to datastore with the following data: {request}"
        )
        response = getattr(self.reader, route)(request)
        if lock_result:
            self.lock_collection_fields_from_filter(
                collection, filter, response.get("position")
            )
        return response[route]

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]:
        return self._minmax(
            "min", collection, filter, field, get_deleted_models, lock_result
        )

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]:
        return self._minmax(
            "max", collection, filter, field, get_deleted_models, lock_result
        )

    @handle_datastore_errors
    def _minmax(
        self,
        route: str,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour,
        lock_result: bool,
    ) -> Optional[int]:
        full_filter = self.apply_deleted_models_behaviour_to_filter(
            filter, get_deleted_models
        )
        request = MinMaxRequest(
            collection=str(collection), filter=full_filter, field=field
        )
        self.logger.debug(
            f"Start {route.upper()} request to datastore with the following data: {request}"
        )
        response = getattr(self.reader, route)(request)
        if lock_result:
            self.lock_collection_fields_from_filter(
                collection, filter, response.get("position"), field
            )
        return response[route]

    def history_information(
        self, fqids: List[str]
    ) -> Dict[str, List[HistoryInformation]]:
        request = HistoryInformationRequest(fqids=fqids)
        self.logger.debug(
            f"Start HISTORY_INFORMATION request to datastore with the following data: {request}"
        )
        return dict(self.reader.history_information(request))

    def lock_collection_fields_from_filter(
        self,
        collection: Collection,
        filter: Filter,
        position: Optional[int],
        additional_field: Optional[str] = None,
    ) -> None:
        if position is None:
            raise DatastoreException("Invalid response from datastore.")
        fields = set()
        filter_visitor(filter, lambda fo: fields.add(fo.field))
        if "meeting_id" not in fields:
            self.logger.debug(
                "Locking a collection field with a filter which does not contain meeting_id!"
            )
        if additional_field:
            fields.add(additional_field)
        for field in fields:
            cf = collectionfield_from_collection_and_field(collection, field)
            self.update_locked_fields(cf, {"position": position, "filter": filter})

    def apply_deleted_models_behaviour_to_filter(
        self, filter: Filter, get_deleted_models: DeletedModelsBehaviour
    ) -> Filter:
        """
        Takes the given filter and wraps an AND-Filter based on the given
        DeletedModelsBehaviour around it.
        """
        if get_deleted_models == DeletedModelsBehaviour.ALL_MODELS:
            return filter

        deleted_models_filter = FilterOperator(
            "meta_deleted",
            "=",
            get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED,
        )
        return And(filter, deleted_models_filter)

    def update_locked_fields_from_mapped_fields(
        self, fqid: FullQualifiedId, position: int, mapped_fields: Optional[Set[str]]
    ) -> None:
        if mapped_fields is not None:
            for field in mapped_fields:
                if not field.startswith("meta_"):
                    self.update_locked_fields(
                        fqfield_from_fqid_and_field(fqid, field),
                        position,
                    )
        else:
            self.update_locked_fields(fqid, position)

    def update_locked_fields(
        self,
        key: Union[FullQualifiedId, FullQualifiedField, CollectionField],
        lock: Union[int, CollectionFieldLockWithFilter],
    ) -> None:
        """
        Updates the locked_fields map by adding the new value for the given FQId or
        FQField. To work properly in case of retry/reread we have to accept the new value always.
        """
        if not isinstance(lock, int) and not COLLECTIONFIELD_PATTERN.match(key):
            raise DatastoreException(
                "You can only lock collection fields with a filter"
            )
        new_value: CollectionFieldLock = lock
        if old_pos := self.locked_fields.get(str(key)):
            if isinstance(old_pos, int) and isinstance(lock, int):
                # keep the smaller position
                if old_pos <= lock:
                    return
            else:
                # if we currently have a position saved, transform it into a list with one entry
                if isinstance(old_pos, int):
                    old_pos = [{"position": old_pos}]
                elif not isinstance(old_pos, list):
                    old_pos = [old_pos]
                # add the new lock to the list
                if isinstance(lock, int):
                    new_value = old_pos + [{"position": lock}]
                else:
                    new_value = old_pos + [lock]
        self.locked_fields[str(key)] = new_value

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

    def write(self, write_requests: Union[List[WriteRequest], WriteRequest]) -> None:
        if isinstance(write_requests, WriteRequest):
            write_requests = [write_requests]
        command = commands.Write(write_requests=write_requests)
        self.logger.debug(
            f"Start WRITE request to datastore with the following data: "
            f"Write request: {write_requests}"
        )
        self.retrieve(command)

    def write_without_events(self, write_request: WriteRequest) -> None:
        command = commands.WriteWithoutEvents(write_requests=[write_request])
        self.logger.debug(
            f"Start WRITE_WITHOUT_EVENTS request to datastore with the following data: "
            f"Write request: {write_request}"
        )
        self.retrieve(command)

    def truncate_db(self) -> None:
        command = commands.TruncateDb()
        self.logger.debug("Start TRUNCATE_DB request to datastore")
        self.retrieve(command)

    def get_everything(self) -> Dict[Collection, Dict[int, PartialModel]]:
        command = commands.GetEverything()
        self.logger.debug("Get Everything from datastore.")
        return self.retrieve(command)

    def delete_history_information(self) -> None:
        command = commands.DeleteHistoryInformation()
        self.logger.debug("Delete history information send to datastore.")
        self.retrieve(command)

    def reset(self, hard: bool = True) -> None:
        self.locked_fields = {}
