from collections import defaultdict
from collections.abc import Sequence
from typing import Any, cast

from psycopg import Connection, rows

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    ArrayField,
    Field,
    GenericRelationListField,
    RelationListField,
)
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
from openslides_backend.shared.filters import (
    And,
    Filter,
    FilterOperator,
    Not,
    Or,
    filter_visitor,
)
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
)
from ...shared.typing import DeletedModel, Model, ModelMap
from ..database.commands import GetManyRequest
from ..database.interface import Database
from .database_reader import DatabaseReader
from .database_writer import DatabaseWriter
from .mapped_fields import MappedFields

MappedFieldsPerCollectionAndId = dict[str, dict[Id, list[str]]]
VALID_AGGREGATE_FUNCTIONS = ["min", "max", "count"]


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

    _changed_models: ModelMap
    locked_fields: dict[str, CollectionFieldLock]

    def __init__(
        self, connection: Connection[rows.DictRow], logging: LoggingModule, env: Env
    ) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self._changed_models = defaultdict(lambda: defaultdict(dict))
        self._to_be_deleted: set[FullQualifiedId] = set()
        self._to_be_deleted_for_protected: set[FullQualifiedId] = set()
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
        collection, id_ = collection_and_id_from_fqid(fqid)
        if replace or isinstance(instance, DeletedModel):
            self._changed_models[collection][id_] = instance
        else:
            self._changed_models[collection][id_].update(instance)
        if "id" not in self._changed_models[collection][id_]:
            self._changed_models[collection][id_]["id"] = id_

    def apply_to_be_deleted(self, fqid: FullQualifiedId) -> None:
        """
        The model will be marked as to be deleted.
        This will not be undone when it is marked as deleted.
        """
        self._to_be_deleted.add(fqid)

    def apply_to_be_deleted_for_protected(self, fqid: FullQualifiedId) -> None:
        """
        The model will be marked as to be deleted.
        This will not be undone when it is marked as deleted.
        Only used for protected models deletion.
        """
        self._to_be_deleted_for_protected.add(fqid)

    def get_changed_model(
        self, collection_or_fqid: str, id_: int | None = None
    ) -> PartialModel:
        if not id_:
            collection_or_fqid, id_ = collection_and_id_from_fqid(collection_or_fqid)
        return self._changed_models[collection_or_fqid][id_]

    def get_changed_models(self, collection: str) -> dict[Id, PartialModel]:
        return self._changed_models.get(collection, dict())

    def is_to_be_deleted(self, fqid: FullQualifiedId) -> bool:
        """
        Returns if the model was ever marked for deletion.
        """
        return fqid in self._to_be_deleted

    def is_to_be_deleted_for_protected(self, fqid: FullQualifiedId) -> bool:
        """
        Returns if the model was ever marked for deletion.
        Only used for protected models deletion.
        """
        return fqid in self._to_be_deleted_for_protected or fqid in self._to_be_deleted

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
        if use_changed_models and (
            changed_model := self._changed_models[collection][id_]
        ):
            if self.is_deleted(fqid):
                raise ModelDoesNotExist(fqid)
            # TODO do deep copy instead
            # TODO check if the id is always wanted in case of mapped fields
            changed_model_copy = (
                {
                    k: changed_model[k]
                    for k in mapped_fields + ["id"]
                    if k in changed_model
                }
                if mapped_fields
                else dict(changed_model)
            )
            # fetch result from changed models
            if mapped_fields:
                missing_fields = [
                    field for field in mapped_fields if field not in changed_model_copy
                ]
            else:
                missing_fields = [field for field in changed_model_copy.keys()]
            if not missing_fields:
                # nothing to do, we've got the full model
                return changed_model_copy
            else:
                # overwrite params and fetch missing fields from db
                mapped_fields = missing_fields
                # we only raise an exception now if the model is not present in the changed_models at all
                raise_exception = (
                    raise_exception and id_ not in self._changed_models[collection]
                )
        else:
            changed_model_copy = dict()

        try:
            # TODO use these functions in other places of the ExtendedDatabase too
            if self.is_new(fqid):
                # if the model is new, we know it does not exist in the datastore and can directly throw
                # an exception or return an empty result
                if raise_exception:
                    error_message = f"fqid: {fqid} is new."
                    # logger.debug(error_message)
                    raise DatabaseException(error_message)
                return changed_model_copy
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
                    raise ModelDoesNotExist(fqid)
        except DatabaseException as e:
            if raise_exception:
                raise e
            else:
                return dict()
        result.update(changed_model_copy)
        return {k: v for k, v in result.items() if v is not None}

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
                # delete fields set to None in changed models
                for (
                    collection,
                    mapped_fields_per_id,
                ) in mapped_fields_per_collection_and_id.items():
                    for id_, mapped_fields in mapped_fields_per_id.items():
                        for field in mapped_fields:
                            if (
                                collection in results
                                and id_ in results[collection]
                                and field in results[collection][id_]
                                and results[collection][id_][field] is None
                            ):
                                del results[collection][id_][field]
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
                if self.is_deleted(fqid_from_collection_and_id(collection, id_)):
                    raise ModelDoesNotExist(
                        fqid_from_collection_and_id(collection, id_)
                    )
                if changed_model := self._changed_models[collection].get(id_, dict()):
                    results[collection][id_]["id"] = id_
                    if mapped_fields:
                        for field in mapped_fields:
                            if field in changed_model or changed_model.get("meta_new"):
                                results[collection][id_][field] = changed_model.get(
                                    field, None
                                )
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
        if not filter_:
            result = self.database_reader.get_all(
                collection, MappedFields(mapped_fields), lock_result
            )
        else:
            if use_changed_models and (
                changed_models_collection := self._changed_models[collection]
            ):
                fully_matched_ids = []
                partially_matched_ids = []
                except_by_changed_models = set()
                # collect all relevant fields from the filter operators
                filter_fields = set()
                filter_visitor(filter_, lambda fo: filter_fields.add(fo.field))
                # identify and get models that could lead to matches in conjunction with the database
                # we are currently slightly overmatching but we filter again on the full model
                for id_, changed_model in changed_models_collection.items():
                    if isinstance(
                        changed_model, DeletedModel
                    ) or self._model_fails_filter(
                        changed_model,
                        filter_,
                    ):
                        except_by_changed_models.add(id_)
                    # TODO decide whether it would be on average faster to not do the full
                    # check here and continue with more partially_matched_ids instead
                    elif all(
                        filter_field in changed_model for filter_field in filter_fields
                    ):
                        if self._model_fits_filter(changed_model, filter_):
                            fully_matched_ids.append(id_)
                    elif self._model_fits_subfilter(changed_model, filter_):
                        partially_matched_ids.append(id_)
                if partially_matched_ids:
                    partially_matched_models = self.database_reader.get_many(
                        [
                            GetManyRequest(
                                collection, partially_matched_ids, list(filter_fields)
                            )
                        ],
                        lock_result,
                    ).get(collection, dict())
                # update db models and calculate exact matching
                for id_ in partially_matched_ids:
                    # TODO update seems unnecassary and should be treated by ex_dbs get_many
                    if id_ in partially_matched_models:
                        partially_matched_models[id_].update(
                            changed_models_collection[id_]
                        )
                    else:
                        partially_matched_models[id_] = changed_models_collection[id_]
                    if self._model_fits_filter(partially_matched_models[id_], filter_):
                        fully_matched_ids.append(id_)
                    # we can and should exclude here since the models are not wanted
                    # as they could fit without the changed models data
                    else:
                        except_by_changed_models.add(id_)
                # update filter for fast query of mapped fields
                filter_ = And(
                    Not(FilterOperator("id", "in", list(except_by_changed_models))),
                    Or(FilterOperator("id", "in", fully_matched_ids), filter_),
                )
            result = self.database_reader.filter(
                collection, filter_, MappedFields(mapped_fields), lock_result
            )
            if use_changed_models:
                for id_, changed_model in changed_models_collection.items():
                    # new models will not be in the filter result. So we need to search them in the before matched ids and add a dict.
                    if changed_model.get("meta_new") and id_ in fully_matched_ids:
                        result[id_] = dict()
                    if id_ in result:
                        for mapped_field in mapped_fields:
                            if mapped_field in changed_model:
                                result[id_][mapped_field] = changed_model[mapped_field]
                            elif changed_model.get("meta_new"):
                                result[id_][mapped_field] = None
        return result

    def exists(
        self,
        collection: Collection,
        filter_: Filter | None,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool:
        return self.count(collection, filter_, lock_result, use_changed_models) > 0

    def aggregate(
        self,
        method: str,
        collection: Collection,
        filter_: Filter | None,
        field_or_star: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        if method not in VALID_AGGREGATE_FUNCTIONS:
            raise BadCodingException(f"Invalid aggregate function: {method}")
        if use_changed_models and self._changed_models[collection]:
            match method:
                case "count":
                    return len(self.filter(collection, filter_, [], lock_result))
                case "min" | "max":
                    response = self.filter(
                        collection,
                        filter_,
                        [field_or_star],
                        lock_result,
                    )
                    if response and (
                        response_values := [
                            model[field_or_star]
                            for model in response.values()
                            if model[field_or_star] is not None
                        ]
                    ):
                        if method == "max":
                            return max(response_values)
                        else:
                            return min(response_values)
                    else:
                        return None
                case _:
                    raise BadCodingException(
                        f"Invalid aggregate function: {method} frfr"
                    )
        else:
            return self.database_reader.aggregate(
                collection, filter_, method, field_or_star, lock_result
            )

    def count(
        self,
        collection: Collection,
        filter_: Filter | None,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int:
        return cast(
            int,
            self.aggregate(
                "count", collection, filter_, "*", lock_result, use_changed_models
            ),
        )

    def min(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        return self.aggregate(
            "min", collection, filter_, field, lock_result, use_changed_models
        )

    def max(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None:
        return self.aggregate(
            "max", collection, filter_, field, lock_result, use_changed_models
        )

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        collection, id_ = collection_and_id_from_fqid(fqid)
        return isinstance(self._changed_models[collection].get(id_), DeletedModel)

    def is_new(self, fqid: FullQualifiedId) -> bool:
        collection, id_ = collection_and_id_from_fqid(fqid)
        return self._changed_models[collection].get(id_, {}).get("meta_new") is True

    def reset(self, hard: bool = True) -> None:
        if hard:
            self._changed_models.clear()

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

        for write_request in write_requests:
            for event in write_request.events:
                if fqid := event.get("fqid"):
                    if len(fqid) > FQID_MAX_LEN:
                        raise InvalidFormat(
                            f"fqid {fqid} is too long (max: {FQID_MAX_LEN})"
                        )
                    collection, id_ = collection_and_id_from_fqid(fqid)
                elif event["type"] == EventType.Create:
                    if event.get("collection"):
                        collection = event["collection"]
                    else:
                        raise InvalidFormat(
                            "Event must contain either fqid or collection."
                        )
                else:
                    raise InvalidFormat("Event must contain fqid.")
                if event["type"] != EventType.Delete:
                    # TODO try to remove this if below TODO is completed
                    if not event.get("fields"):
                        event["fields"] = {}
                if event["type"] == EventType.Update:
                    # TODO does this lead to any unexpected and unwanted exceptions in the backend tests?
                    if not (event.get("fields") or (event.get("list_fields"))):
                        raise InvalidFormat("No fields given.")
                if list_fields := event.get("list_fields", ListFields()):
                    # TODO there should be a performance improvement by generating a tuple with the field that can then be used by the database_writer
                    collection_cls = model_registry[collection]()
                    for add_or_remove_dict in list_fields.values():
                        for field_name in cast(dict, add_or_remove_dict):
                            field: Field = collection_cls.get_field(field_name)
                            # TODO in future we should assert that RelationLists will not be sent anymore
                            if not isinstance(
                                field,
                                (
                                    ArrayField,
                                    RelationListField,
                                    GenericRelationListField,
                                ),
                            ):
                                raise InvalidFormat(
                                    f"'{field_name}' used for 'list_fields' 'remove' or 'add' is no array in database."
                                )
        # TODO there should be an improvement by sending each event directly to the database_writers write_event
        fqids = self.database_writer.write(write_requests)
        self.logger.debug(
            f"Start WRITE request to database with the following data: "
            f"Write request: {write_requests}"
        )
        return fqids

    def truncate_db(self) -> None:
        self.database_writer.truncate_db()

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

    def _model_fits_subfilter(
        self, model: Model, filter_: Filter, negation: bool = False
    ) -> bool:
        """This method returns True if one subfilter could lead the whole filter to return True if all other fields did too."""
        if isinstance(filter_, Not):
            return self._model_fits_subfilter(model, filter_.not_filter, not negation)
        elif isinstance(filter_, Or):
            return any(
                self._model_fits_subfilter(model, part, negation)
                for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return any(
                self._model_fits_subfilter(model, part, negation)
                for part in filter_.and_filter
            )
        else:
            return negation ^ self._model_fits_operator_filter(model, filter_)

    def _model_fails_filter(
        self, model: Model, filter_: Filter, negation: bool = False
    ) -> bool:
        """This method returns True if one subfilter would lead the whole filter to return False."""
        if isinstance(filter_, Not):
            return self._model_fails_filter(model, filter_.not_filter, not negation)
        elif isinstance(filter_, Or):
            if negation:
                return any(
                    self._model_fails_filter(model, part, negation)
                    for part in filter_.or_filter
                )
            else:
                return all(
                    self._model_fails_filter(model, part, negation)
                    for part in filter_.or_filter
                )
        elif isinstance(filter_, And):
            if negation:
                return all(
                    self._model_fails_filter(model, part, negation)
                    for part in filter_.and_filter
                )
            else:
                return any(
                    self._model_fails_filter(model, part, negation)
                    for part in filter_.and_filter
                )
        else:
            if filter_.field not in model:
                # if the model is not in the database the value should be assumed to be the default TODO
                if model.get("meta_new"):
                    model = {filter_.field: None}
                else:
                    return False
            return not negation ^ self._model_fits_operator_filter(model, filter_)

    def _model_fits_filter(self, model: Model, filter_: Filter) -> bool:
        if isinstance(filter_, Not):
            return not self._model_fits_filter(model, filter_.not_filter)
        elif isinstance(filter_, Or):
            return any(
                self._model_fits_filter(model, part) for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return all(
                self._model_fits_filter(model, part) for part in filter_.and_filter
            )
        else:
            return self._model_fits_operator_filter(model, filter_)

    def _model_fits_operator_filter(
        self, model: Model, filter_: FilterOperator
    ) -> bool:
        field_value = model.get(filter_.field)
        if field_value is None or filter_.value is None:
            if filter_.operator == "=":
                return field_value is filter_.value
            elif filter_.operator == "!=":
                return field_value is not filter_.value
            return False
        match filter_.operator:
            case "!=":
                return field_value != filter_.value
            case "=":
                return field_value == filter_.value
            case "<=":
                return field_value <= filter_.value
            case "<":
                return field_value < filter_.value
            case ">=":
                return field_value >= filter_.value
            case ">":
                return field_value > filter_.value
            case "in":
                return field_value in filter_.value
            case "has":
                return filter_.value in field_value
            case "~=":
                return field_value.lower() == filter_.value.lower()
            case "%=":
                raise NotImplementedError("Operator %= is not supported")
            case default:
                raise NotImplementedError(f"Operator {default} is not supported")
