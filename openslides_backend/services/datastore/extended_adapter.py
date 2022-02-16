import builtins
import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Tuple

from datastore.shared.postgresql_backend import SqlQueryHelper
from datastore.shared.util import DeletedModelsBehaviour

from ...shared.exceptions import DatastoreException
from ...shared.filters import And, Filter, FilterOperator
from ...shared.interfaces.logging import LoggingModule
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.typing import DeletedModel, ModelMap
from .adapter import DatastoreAdapter
from .commands import GetManyRequest
from .handle_datastore_errors import raise_datastore_error
from .interface import Engine, LockResult, PartialModel

MODEL_FIELD_SQL = "data->>%s"
COMPARISON_VALUE_SQL = "%s::text"


MappedFieldsPerFqid = Dict[FullQualifiedId, List[str]]


class ExtendedDatastoreAdapter(DatastoreAdapter):
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

    def __init__(self, engine: Engine, logging: LoggingModule) -> None:
        super().__init__(engine, logging)
        self.changed_models = defaultdict(dict)

    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None:
        """
        Adds or replaces the model identified by fqid in the changed_models.
        Automatically adds missing id field.
        """
        if replace or isinstance(instance, DeletedModel):
            self.changed_models[fqid] = instance
        else:
            self.changed_models[fqid].update(instance)
        if "id" not in self.changed_models[fqid]:
            self.changed_models[fqid]["id"] = fqid.id

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel:
        """
        Get the given model.
        changed_models serves as a kind of cache layer of all recently done
        changes - all updates to any model during the action are saved in there.
        The parameter use_changed_models defines whether they are searched or not.
        """
        if use_changed_models:
            if position:
                raise DatastoreException(
                    "Position-based fetching is not possible with changed_models"
                )

            mapped_fields_per_fqid = {fqid: mapped_fields}
            # fetch results from changed models
            results, missing_fields_per_fqid = self._get_many_from_changed_models(
                mapped_fields_per_fqid
            )
            changed_model = results.get(fqid.collection, {}).get(fqid.id, {})
            if not missing_fields_per_fqid:
                # nothing to do, we've got the full mode
                return changed_model
            else:
                # overwrite params and fetch missing fields from db
                mapped_fields = missing_fields_per_fqid[fqid]
                # we only raise an exception now if the model is not present in the changed_models all
                raise_exception = raise_exception and fqid not in self.changed_models

        try:
            if self.is_new(fqid):
                # if the model is new, we know it does not exist in the datastore and can directly throw
                # an exception or return an empty result
                raise_datastore_error({"error": {"fqid": fqid}})
            else:
                result = super().get(
                    fqid,
                    mapped_fields,
                    position,
                    get_deleted_models,
                    lock_result,
                )
        except DatastoreException:
            if raise_exception:
                raise
            else:
                return {}

        if use_changed_models:
            result.update(changed_model)
        return result

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        if use_changed_models:
            if position:
                raise DatastoreException(
                    "Position-based fetching is not possible with changed_models"
                )

            mapped_fields_per_fqid = defaultdict(list)
            for request in get_many_requests:
                if not request.mapped_fields:
                    raise DatastoreException("No mapped fields given")
                for id in request.ids:
                    fqid = FullQualifiedId(request.collection, id)
                    mapped_fields_per_fqid[fqid].extend(list(request.mapped_fields))
            # fetch results from changed models
            results, missing_fields_per_fqid = self._get_many_from_changed_models(
                mapped_fields_per_fqid
            )
            # fetch missing fields in the changed_models from the db and merge into the results
            if missing_fields_per_fqid:
                missing_results = self._fetch_missing_fields_from_datastore(
                    missing_fields_per_fqid, lock_result
                )
                for collection, models in missing_results.items():
                    for id, model in models.items():
                        # we can just update the model with the db fields since they must not have been
                        # present previously
                        results.setdefault(collection, {}).setdefault(id, {}).update(
                            model
                        )
        else:
            results = super().get_many(
                get_many_requests, None, get_deleted_models, lock_result
            )
        return results

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[int, PartialModel]:
        results = super().filter(
            collection, filter, mapped_fields, get_deleted_models, lock_result
        )
        if use_changed_models:
            # apply the changes from the changed_models to the db result
            self._apply_changed_model_updates(
                collection, results, mapped_fields, get_deleted_models
            )
            # find results which are only present in the changed_models
            changed_results = self._filter_additional_models(
                collection, filter, mapped_fields
            )
            # apply these results and find fields which are missing in the changed_models
            missing_fields_per_fqid = self._update_results_and_get_missing_fields(
                collection, results, changed_results, mapped_fields
            )
            # fetch missing fields from the db and merge both results
            if missing_fields_per_fqid:
                missing_results = self._fetch_missing_fields_from_datastore(
                    missing_fields_per_fqid, lock_result
                )
                for id, model in missing_results[collection].items():
                    # we can just update the model with the db fields since they must not have been
                    # present previously
                    results.setdefault(id, {}).update(model)
        return results

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool:
        if not use_changed_models:
            return super().exists(collection, filter, get_deleted_models, lock_result)
        else:
            return self.count(collection, filter, get_deleted_models, lock_result) > 0

    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int:
        if not use_changed_models:
            return super().count(collection, filter, get_deleted_models, lock_result)
        else:
            results = self.filter(
                collection, filter, ["id"], get_deleted_models, lock_result
            )
            return len(results)

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]:
        return self._extended_minmax(
            collection,
            filter,
            field,
            get_deleted_models,
            lock_result,
            use_changed_models,
            "min",
        )

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]:
        return self._extended_minmax(
            collection,
            filter,
            field,
            get_deleted_models,
            lock_result,
            use_changed_models,
            "max",
        )

    def _extended_minmax(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour,
        lock_result: bool,
        use_changed_models: bool,
        mode: Literal["min", "max"],
    ) -> Optional[int]:
        if not use_changed_models:
            return getattr(super(), mode)(
                collection, filter, field, get_deleted_models, lock_result
            )
        else:
            full_filter = And(filter, FilterOperator(field, "!=", None))
            models = self.filter(
                collection, full_filter, [field], get_deleted_models, lock_result
            )
            comparable_results = [
                model[field]
                for model in models.values()
                if self._comparable(model.get(field), 0)
            ]
            if comparable_results:
                return getattr(builtins, mode)(comparable_results)
            else:
                return None

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        return isinstance(self.changed_models.get(fqid), DeletedModel)

    def is_new(self, fqid: FullQualifiedId) -> bool:
        return self.changed_models.get(fqid, {}).get("meta_new") is True

    def reset(self) -> None:
        super().reset()
        self.changed_models.clear()

    def _filter_additional_models(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
    ) -> Dict[int, Dict[str, Any]]:
        """
        Uses the datastore's SqlQueryHelper to build an SQL query for the given filter, transforms it into valid python
        code and then executes it.
        """
        # Build sql query for this filter. The arguments array contains the replacements for all %s in the query in the
        # correct order.
        query_helper = SqlQueryHelper()
        arguments: List[str] = []
        sql_query = query_helper.build_filter_str(filter, arguments)

        # transform query into valid python code
        filter_code = sql_query.lower().replace("null", "None").replace(" = ", " == ")
        # regex for all FilterOperators which were translated by the SqlQueryHelper
        regex = f"{MODEL_FIELD_SQL} (<|<=|>=|>|==|!=|is|is not) ({COMPARISON_VALUE_SQL}|None)"
        matches = re.findall(regex, filter_code)
        # this will hold all items from arguments, but correctly formatted for python and enhanced with validity checks
        formatted_args = []
        i = 0
        for match in matches:
            # for these operators, ensure that the model field is actually comparable to prevent TypeErrors
            if match[0] in ("<", "<=", ">=", ">"):
                val_str = (
                    arguments[i + 1]
                    if isinstance(arguments[i + 1], (int, float))
                    else repr(arguments[i + 1])
                )
                formatted_args.append(
                    f'self._comparable(model.get("{arguments[i]}"), {val_str}) and model.get("{arguments[i]}")'
                )
            else:
                formatted_args.append(f'model.get("{arguments[i]}")')
            i += 1
            # if comparison happens with a value, append it as well
            if match[1] == COMPARISON_VALUE_SQL:
                formatted_args.append(repr(arguments[i]))
                i += 1
        # replace SQL placeholders and SQL specific code with the formatted python snippets
        filter_code = filter_code.replace(MODEL_FIELD_SQL, "{}").replace(
            COMPARISON_VALUE_SQL, "{}"
        )
        filter_code = filter_code.format(*formatted_args)
        # run eval with the generated code
        filter_code = (
            "{model['id']: {field: model[field] for field in mapped_fields if field in model} for fqid, model in self.changed_models.items() if fqid.collection == collection and ("
            + filter_code
            + ")}"
        )
        scope = locals()
        results = eval(filter_code, scope)
        return deepcopy(results)

    def _comparable(self, a: Any, b: Any) -> bool:
        """
        Tries to compare a and b. If they are not comparable, the resulting TypeError is caught and False is returned.
        Only < is tested since generally either all comparisons are implemented or none, so it is sufficient to only
        test one.
        """
        try:
            a < b
            return True
        except TypeError:
            return False

    def _get_many_from_changed_models(
        self,
        mapped_fields_per_fqid: MappedFieldsPerFqid,
    ) -> Tuple[Dict[Collection, Dict[int, PartialModel]], MappedFieldsPerFqid]:
        """
        Returns a dictionary of the changed models for the given collections together with all
        missing fields.
        """
        results: Dict[Collection, Dict[int, PartialModel]] = defaultdict(dict)
        missing_fields_per_fqid: MappedFieldsPerFqid = defaultdict(list)
        for fqid, mapped_fields in mapped_fields_per_fqid.items():
            if fqid in self.changed_models:
                for field in mapped_fields:
                    if field in self.changed_models[fqid]:
                        results[fqid.collection].setdefault(fqid.id, {})[
                            field
                        ] = self.changed_models[fqid][field]
                    else:
                        missing_fields_per_fqid[fqid].append(field)
            else:
                missing_fields_per_fqid[fqid] = mapped_fields
        return (results, missing_fields_per_fqid)

    def _apply_changed_model_updates(
        self,
        collection: Collection,
        results: Dict[int, PartialModel],
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour,
    ) -> None:
        # create temp list of ids to be able to change the models dict in place
        for id in list(results.keys()):
            fqid = FullQualifiedId(collection, id)
            if fqid in self.changed_models:
                is_deleted = self.is_deleted(fqid)
                if (
                    not is_deleted
                    and get_deleted_models != DeletedModelsBehaviour.ONLY_DELETED
                ):
                    for field in mapped_fields:
                        if field in self.changed_models[fqid]:
                            results[id][field] = self.changed_models[fqid][field]
                elif not (
                    is_deleted
                    and get_deleted_models != DeletedModelsBehaviour.NO_DELETED
                ):
                    del results[id]

    def _update_results_and_get_missing_fields(
        self,
        collection: Collection,
        results: Dict[int, PartialModel],
        changed_results: Dict[int, PartialModel],
        mapped_fields: List[str],
    ) -> MappedFieldsPerFqid:
        missing_fields_per_fqid = defaultdict(list)
        for id, model in changed_results.items():
            if id in results:
                # id exists in both results: just update with new values
                results[id].update(model)
            else:
                # id only exists in new values: maybe some fields are missing and we have to fetch them
                results[id] = model
                fqid = FullQualifiedId(collection, id)
                missing_fields = [
                    field for field in mapped_fields if field not in model
                ]
                if missing_fields:
                    missing_fields_per_fqid[fqid] = missing_fields
        return missing_fields_per_fqid

    def _fetch_missing_fields_from_datastore(
        self, missing_fields_per_fqid: MappedFieldsPerFqid, lock_result: bool
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        get_many_requests = [
            GetManyRequest(fqid.collection, [fqid.id], fields)
            for fqid, fields in missing_fields_per_fqid.items()
        ]
        results = super().get_many(
            get_many_requests, None, DeletedModelsBehaviour.ALL_MODELS, lock_result
        )
        return results
