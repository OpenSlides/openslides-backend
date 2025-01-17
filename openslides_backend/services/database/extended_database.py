from collections import defaultdict
from collections.abc import Sequence
from typing import Any, ContextManager

from openslides_backend.shared.interfaces.collection_field_lock import (
    CollectionFieldLock,
)
from openslides_backend.shared.typing import LockResult, PartialModel

from ...shared.exceptions import BadCodingException, DatabaseException, InvalidFormat
from ...shared.filters import Filter
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import (
    Collection,
    FullQualifiedId,
    Id,
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...shared.typing import DeletedModel, ModelMap
from ..database.commands import GetManyRequest
from ..database.interface import Database
from .database_reader import DatabaseReader

# from openslides_backend.shared.patterns import (
#     Collection,
#     Field,
#     FullQualifiedId,
#     Id,
#     Position,
#     collection_and_id_from_fqid,
# )
MappedFieldsPerCollectionAndId = dict[str, dict[Id, list[str]]]


class ExtendedDatabase(Database):
    """
    Subclass of the datastore adapter to extend the functions with the usage of the changed_models.

    Restrictions:
    -   get_deleted_models only works one way with the changed_models: if the model was not deleted
        in the datastore, but is deleted in the changed_models. The other way around does not work
        since a deleted model in the changed_models is marked via DeletedModel() and does not store
        any data.
    -   all filter-based requests may take two calls to the datastore to succeed. The first call is
        always necessary, since the changed_models are never complete. If, however, a model in the
        changed_models matches the filter which it did not in the database AND some fields are
        missing in the changed_models which are needed through the mapped_fields, a second request
        is needed to fetch the missing fields. This can be circumvented by always storing (more or
        less) "full" models in the changed_data, meaning all relevant fields which are requested in
        future calls are present. This is the case for most applications in the backend.
    -   filters are only evaluated separately on the changed_models and the datastore. If, for
        example, a model in the datastore does not fit the filter, but through a change in the
        changed_models would fit it, BUT does not fit the filter from the changed_models alone, it
        is not found. Example:
        datastore content: {"f": 1, "g": 1}
        changed_models: {"f": 2}
        filter: f = 2 and g = 1
        This also applies in the reverse direction: If the datastore content of a model matches the
        filter, but it is invalidated through a change in the changed_models, it is still found and
        returned with the new fields from the changed_models. This may lead to unexpected results by
        including a model in the results which does not fit the given filter. This could be
        circumvented by applying the filter again after building the result and removing all models
        which do not fit it anymore.
        For performance as well as practical reasons, this is not implemented. In practice, filters
        are only applied to "static" fields which do not changed during a request, e.g.
        `meeting_id`, `list_of_speakers_id` etc. So this should not be a problem.
    """

    changed_models: ModelMap
    locked_fields: dict[str, CollectionFieldLock]

    def __init__(self, logging: LoggingModule, env: Env) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.changed_models: dict[str, dict[str, Any]] = defaultdict(dict)
        self.database_reader = DatabaseReader()
        # self.database_writer = DatabaseWriter()

    def get_database_context(self) -> ContextManager[None]:
        # TODO what are the requirements?
        return self.database_reader.get_database_context()

    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None:
        """
        Adds or replaces the model identified by fqid in the changed_models.
        Automatically adds missing id field.
        """
        if replace:
            self.changed_models[fqid] = instance
        else:
            self.changed_models[fqid].update(instance)
        if "id" not in self.changed_models[fqid]:
            self.changed_models[fqid]["id"] = id_from_fqid(fqid)

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str] | None = None,
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel:
        """
        Get the given model. This extends the read and write operations respecting
        the changes saved in changed_models.
        changed_models serves as a kind of cache layer of all recently done
        changes - all updates to any model during the action are saved in there.
        The parameter use_changed_models defines whether they are searched or not.
        """
        if fqid is None:
            raise BadCodingException("No fqid. Offer at least one fqid.")
        try:
            collection, id_ = collection_and_id_from_fqid(fqid)
        except IndexError as e:
            raise InvalidFormat(f"Invalid fqid format. {e}")
        if use_changed_models and (changed_model := self.changed_models.get(fqid)):
            # fetch result from changed models
            if mapped_fields:
                missing_fields = [
                    field for field in mapped_fields if field not in changed_model
                ]
            else:
                missing_fields = [field for field in changed_model.keys()]
            if not missing_fields:
                # nothing to do, we've got the full model
                return changed_model
            else:
                # overwrite params and fetch missing fields from db
                mapped_fields = missing_fields
                # we only raise an exception now if the model is not present in the changed_models at all
                raise_exception = raise_exception and fqid not in self.changed_models
        else:
            changed_model = dict()

        try:
            if self.is_new(fqid):
                # if the model is new, we know it does not exist in the datastore and can directly throw
                # an exception or return an empty result
                if raise_exception:
                    error_message = f"fqid: {fqid} is new."
                    # logger.debug(error_message)
                    raise DatabaseException(error_message)
                return changed_model
            else:
                result = (
                    self.database_reader.get_many(
                        [GetManyRequest(collection, [id_], mapped_fields)],
                        lock_result,
                    )
                    .get(collection, {})
                    .get(id_)
                )
                if not result:
                    return {}
        except DatabaseException as e:
            if raise_exception:
                raise e
            else:
                return dict()
        result.update(changed_model)
        return result

    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        lock_result: LockResult = True,
        use_changed_models: bool = True,
    ) -> dict[Collection, dict[int, PartialModel]]:
        if use_changed_models:
            mapped_fields_per_collection_and_id: dict[str, dict[int, Any]] = (
                defaultdict(dict)
            )
            for request in get_many_requests:
                if not request.mapped_fields:
                    raise DatabaseException("No mapped fields given.")
                collection = request.collection
                for id_ in request.ids:
                    mapped_fields_per_collection_and_id[collection][id_] = list(
                        request.mapped_fields
                    )
            # fetch results from changed models
            results, missing_fields_per_collection_and_id = (
                self._get_many_from_changed_models(mapped_fields_per_collection_and_id)
            )
            # fetch missing fields in the changed_models from the db and merge into the results
            if missing_fields_per_collection_and_id:
                get_many_requests = [
                    GetManyRequest(collection, [id_], fields)
                    for collection, id_fields_dict in missing_fields_per_collection_and_id.items()
                    for id_, fields in id_fields_dict.items()
                ]
                missing_results = self.database_reader.get_many(
                    get_many_requests, lock_result
                )
                for collection, models in missing_results.items():
                    for id_, model in models.items():
                        # we can just update the model with the db fields since they must not have been
                        # present previously
                        results.setdefault(collection, {}).setdefault(id_, {}).update(
                            model
                        )
        else:
            results = self.database_reader.get_many(get_many_requests, lock_result)
        return results

    def _get_many_from_changed_models(
        self,
        mapped_fields_per_collection_and_id: MappedFieldsPerCollectionAndId,
    ) -> tuple[
        dict[Collection, dict[int, PartialModel]], MappedFieldsPerCollectionAndId
    ]:
        """
        Returns a dictionary of the changed models for the given collections together with all
        missing fields.
        """
        results: dict[Collection, dict[int, PartialModel]] = defaultdict(
            lambda: defaultdict(dict)
        )
        missing_fields_per_collection_and_id: MappedFieldsPerCollectionAndId = (
            defaultdict(lambda: defaultdict(list))
        )
        for (
            collection,
            models_mapped_fields,
        ) in mapped_fields_per_collection_and_id.items():
            for id_, mapped_fields in models_mapped_fields.items():
                if (
                    fqid := fqid_from_collection_and_id(collection, id_)
                ) in self.changed_models:
                    changed_model = self.changed_models[fqid]
                    if mapped_fields:
                        for field in mapped_fields:
                            if field in changed_model:
                                results[collection][id_][field] = changed_model[field]
                            else:
                                missing_fields_per_collection_and_id[collection][
                                    id_
                                ].append(field)
                    else:
                        # assuming that whole model is needed and we want that?
                        results[collection][id_] = changed_model
                        missing_fields_per_collection_and_id[collection][id_] = []
                else:
                    missing_fields_per_collection_and_id[collection][
                        id_
                    ] = mapped_fields
        return (results, missing_fields_per_collection_and_id)

    def get_all(
        self,
        collection: Collection,
        mapped_fields: list[str],
        lock_result: bool = True,
    ) -> dict[int, PartialModel]:
        return {}

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: list[str],
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> dict[int, PartialModel]:
        # TODO Implement me!
        return {}

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool:
        # TODO Implement me!
        return False

    def count(
        self,
        collection: Collection,
        filter: Filter,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int:
        # TODO Implement me!
        return 0

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        # TODO Implement me!
        return None

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        # TODO Implement me!
        return None

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        return isinstance(self.changed_models.get(fqid), DeletedModel)

    def is_new(self, fqid: FullQualifiedId) -> bool:
        return self.changed_models.get(fqid, {}).get("meta_new") is True

    def reset(self, hard: bool = True) -> None:
        # super().reset()
        if hard:
            self.changed_models.clear()

    def history_information(self, fqids: list[str]) -> dict[str, list[dict]]:
        return {}

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        return []
        # self.logger.debug(
        #     f"Start RESERVE_IDS request to datastore with the following data: "
        #     f"Collection: {collection}, Amount: {amount}"
        # )
        # response = self.retrieve(command)
        # return response.get("ids")

    def reserve_id(self, collection: Collection) -> int:
        return 0

    #   return self.reserve_ids(collection=collection, amount=1)[0]

    def write(self, write_requests: list[WriteRequest] | WriteRequest) -> None:
        pass
        # if isinstance(write_requests, WriteRequest):
        #     write_requests = [write_requests]
        # command = commands.Write(write_requests=write_requests)
        # self.logger.debug(
        #     f"Start WRITE request to datastore with the following data: "
        #     f"Write request: {write_requests}"
        # )
        # self.retrieve(command)

    def write_without_events(self, write_request: WriteRequest) -> None:
        pass
        # command = commands.WriteWithoutEvents(write_requests=[write_request])
        # self.logger.debug(
        #     f"Start WRITE_WITHOUT_EVENTS request to datastore with the following data: "
        #     f"Write request: {write_request}"
        # )
        # self.retrieve(command)

    def truncate_db(self) -> None: ...

    def get_everything(self) -> dict[Collection, dict[int, PartialModel]]:
        return {}
        # command = commands.GetEverything()
        # self.logger.debug("Get Everything from datastore.")
        # return self.retrieve(command)

    def delete_history_information(self) -> None:
        pass
        # command = commands.DeleteHistoryInformation()
        # self.logger.debug("Delete history information send to datastore.")
        # self.retrieve(command)
