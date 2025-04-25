from collections import defaultdict
from collections.abc import Sequence
from typing import Any, cast

from psycopg import Connection, rows

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import ArrayField, Field
from openslides_backend.services.database.interface import (
    COLLECTION_MAX_LEN,
    FQID_MAX_LEN,
)
from openslides_backend.shared.exceptions import (
    BadCodingException,
    DatabaseException,
    InvalidFormat,
    ModelDoesNotExist,
)
from openslides_backend.shared.filters import And, Filter, Not, Or
from openslides_backend.shared.interfaces.collection_field_lock import (
    CollectionFieldLock,
)
from openslides_backend.shared.typing import LockResult, PartialModel

from ...shared.interfaces.env import Env
from ...shared.interfaces.event import EventType, ListFields
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
from ...shared.typing import DeletedModel, Model, ModelMap
from ..database.commands import GetManyRequest
from ..database.interface import Database
from .database_reader import DatabaseReader
from .database_writer import DatabaseWriter
from .mapped_fields import MappedFields

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

    def __init__(
        self, connection: Connection[rows.DictRow], logging: LoggingModule, env: Env
    ) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.changed_models: dict[FullQualifiedId, PartialModel] = defaultdict(dict)
        self.connection = connection
        self.database_reader = DatabaseReader(self.connection, logging, env)
        self.database_writer = DatabaseWriter(self.connection, logging, env)

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
                    raise ModelDoesNotExist(
                        fqid_from_collection_and_id(collection, id_)
                    )
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
        mapped_fields: list[str] = [],
        lock_result: bool = True,
    ) -> dict[Id, PartialModel]:
        return self.database_reader.get_all(
            collection, MappedFields(mapped_fields), lock_result
        )

    def filter(
        self,
        collection: Collection,
        filter_: Filter | None,
        mapped_fields: list[str],
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> dict[int, PartialModel]:
        if filter_:
            result = self.database_reader.filter(
                collection, filter_, MappedFields(mapped_fields), lock_result
            )
        else:
            result = self.database_reader.get_all(
                collection, MappedFields(mapped_fields), lock_result
            )
        if use_changed_models and self.changed_models:
            for fqid, changed_model in self.changed_models.items():
                if not filter_ or (
                    fqid.startswith(collection)
                    and self.model_fits_filter(changed_model, filter_)
                ):
                    id_ = id_from_fqid(fqid)
                    if id_ in result:
                        result[id_].update(changed_model)
                    else:
                        result[id_] = changed_model
        return result

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
        filter_: Filter | None,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int:
        if use_changed_models and self.changed_models:
            return len(
                self.filter(collection, filter_, [], lock_result, use_changed_models)
            )
        else:
            return self.database_reader.aggregate(
                collection, filter_, "count", "*", lock_result
            )

    def min(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        if use_changed_models and self.changed_models:
            response = self.filter(
                collection, filter_, [field], lock_result, use_changed_models
            )
            return min(model[field] for model in response.values())
        else:
            return self.database_reader.aggregate(
                collection, filter_, "min", field, lock_result
            )

    def max(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        if use_changed_models and self.changed_models:
            response = self.filter(
                collection, filter_, [field], lock_result, use_changed_models
            )
            return max(model[field] for model in response.values())
        else:
            return self.database_reader.aggregate(
                collection, filter_, "max", field, lock_result
            )

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
        self.logger.debug(
            f"Start to reserve ids with the following data: "
            f"Collection: {collection}, Amount: {amount}"
        )
        if not isinstance(amount, int):
            raise InvalidFormat("Amount must be integer.")
        if amount <= 0:
            raise InvalidFormat(f"Amount must be >= 1, not {amount}.")
        if len(collection) > COLLECTION_MAX_LEN or not collection:
            raise InvalidFormat(
                f"Collection length must be between 1 and {COLLECTION_MAX_LEN}"
            )
        return self.database_writer.reserve_ids(collection, amount)

    def reserve_id(self, collection: Collection) -> int:
        return self.reserve_ids(collection=collection, amount=1)[0]

    def write(
        self, write_requests: list[WriteRequest] | WriteRequest
    ) -> list[FullQualifiedId]:
        if isinstance(write_requests, WriteRequest):
            write_requests = [write_requests]

        # prefetch changed models? TODO
        for write_request in write_requests:
            for event in write_request.events:
                if fqid := event.get("fqid"):
                    if len(fqid) > FQID_MAX_LEN:
                        raise InvalidFormat(
                            f"fqid {fqid} is too long (max: {FQID_MAX_LEN})"
                        )
                    collection, id_ = collection_and_id_from_fqid(fqid)
                    if event["type"] != EventType.Delete:
                        if event.get("fields"):
                            event["fields"]["id"] = id_
                        else:
                            event["fields"] = {"id": id_}
                elif event["type"] == EventType.Create:
                    if event.get("collection"):
                        collection = event["collection"]
                    else:
                        raise InvalidFormat(
                            "Event must contain either fqid or collection."
                        )
                else:
                    raise InvalidFormat("Event must contain fqid.")
                if event["type"] == EventType.Update:
                    if not (event.get("fields") or (event.get("list_fields"))):
                        raise InvalidFormat("No fields given.")
                if list_fields := event.get("list_fields", ListFields()):
                    for add_or_remove_dict in list_fields.values():
                        for field_name in cast(dict, add_or_remove_dict):
                            field: Field = model_registry[collection]().get_field(
                                field_name
                            )
                            if not isinstance(field, ArrayField):
                                raise InvalidFormat(
                                    f"'{field_name}' used for 'list_fields' 'remove' or 'add' is no array in database."
                                )

        fqids = self.database_writer.write(write_requests)
        self.logger.debug(
            f"Start WRITE request to database with the following data: "
            f"Write request: {write_requests}"
        )
        return fqids

    def truncate_db(self) -> None: ...

    def get_everything(self) -> dict[Collection, dict[int, Model]]:
        return {
            k: v
            for k, v in {
                collection: self.database_reader.get_all(
                    collection, MappedFields(), False
                )
                for collection in model_registry
                if collection != "motion_statute_paragraph"
            }.items()
            if v
        }

    def delete_history_information(self) -> None:
        pass

    def model_fits_filter(self, model: Model, filter_: Filter) -> bool:
        if isinstance(filter_, Not):
            return not self.model_fits_filter(model, filter_.not_filter)
        elif isinstance(filter_, Or):
            return any(
                self.model_fits_filter(model, part) for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return all(
                self.model_fits_filter(model, part) for part in filter_.and_filter
            )
        else:
            return model.get(filter_.field) == filter_.value
