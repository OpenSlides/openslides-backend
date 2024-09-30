from collections import defaultdict
from copy import deepcopy
from typing import Any

from openslides_backend.datastore.shared.util import DeletedModelsBehaviour

from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.patterns import (Collection, FullQualifiedId,
                                collection_from_fqid,
                                fqid_from_collection_and_id, id_from_fqid)
from ...shared.typing import ModelMap
from .adapter import DatastoreAdapter
from .commands import GetManyRequest
from .interface import Engine, LockResult, MappedFieldsPerFqid, PartialModel


class CacheDatastoreAdapter(DatastoreAdapter):
    cached_models: ModelMap
    cached_missing_fields: dict[FullQualifiedId, set[str]]

    def __init__(self, engine: Engine, logging: LoggingModule, env: Env) -> None:
        super().__init__(engine, logging, env)
        self.cached_models = defaultdict(dict)
        self.cached_missing_fields = defaultdict(set)

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> PartialModel:
        if position or get_deleted_models != DeletedModelsBehaviour.NO_DELETED:
            return super().get(
                fqid,
                mapped_fields,
                position,
                get_deleted_models,
                lock_result,
            )

        mapped_fields_per_fqid = {fqid: mapped_fields}
        # fetch results from cached models
        results, missing_fields_per_fqid = self._get_many_from_cached_models(
            mapped_fields_per_fqid
        )
        cached_model = results[collection_from_fqid(fqid)][id_from_fqid(fqid)]
        if not missing_fields_per_fqid:
            # nothing to do, we've got the full model
            return deepcopy(cached_model)

        result = super().get(
            fqid, missing_fields_per_fqid[fqid], lock_result=lock_result
        )
        if lock_result:
            self._update_cache(fqid, result, missing_fields_per_fqid[fqid])
        result.update(cached_model)
        return deepcopy(result)

    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> dict[Collection, dict[int, PartialModel]]:
        if position or get_deleted_models != DeletedModelsBehaviour.NO_DELETED:
            return super().get_many(
                get_many_requests,
                position,
                get_deleted_models,
                lock_result,
            )

        mapped_fields_per_fqid = defaultdict(list)
        for request in get_many_requests:
            for id in request.ids:
                fqid = fqid_from_collection_and_id(request.collection, id)
                mapped_fields_per_fqid[fqid].extend(list(request.mapped_fields or []))
        # fetch results from cached models
        results, missing_fields_per_fqid = self._get_many_from_cached_models(
            mapped_fields_per_fqid
        )
        # fetch missing fields in the cached_models from the db and merge into the results
        if missing_fields_per_fqid:
            missing_results = self._fetch_missing_fields_from_datastore_for_cache(
                missing_fields_per_fqid, lock_result
            )
            for collection, models in missing_results.items():
                for id, model in models.items():
                    results[collection][id].update(model)
                    if lock_result:
                        fqid = fqid_from_collection_and_id(collection, id)
                        self._update_cache(fqid, model, missing_fields_per_fqid[fqid])
        return deepcopy(results)

    def reset(self, hard: bool = True) -> None:
        super().reset()
        self.cached_models.clear()
        self.cached_missing_fields.clear()

    def _get_many_from_cached_models(
        self,
        mapped_fields_per_fqid: MappedFieldsPerFqid,
    ) -> tuple[dict[Collection, dict[int, PartialModel]], MappedFieldsPerFqid]:
        """
        Returns a dictionary of the cached models for the given collections together with all
        missing fields.
        """
        results: dict[Collection, dict[int, PartialModel]] = defaultdict(
            lambda: defaultdict(dict)
        )
        missing_fields_per_fqid: MappedFieldsPerFqid = defaultdict(list)
        for fqid, mapped_fields in mapped_fields_per_fqid.items():
            if fqid in self.cached_models:
                if mapped_fields:
                    for field in mapped_fields:
                        if field in self.cached_models[fqid]:
                            results[collection_from_fqid(fqid)][id_from_fqid(fqid)][
                                field
                            ] = self.cached_models[fqid][field]
                        elif field not in self.cached_missing_fields[fqid]:
                            missing_fields_per_fqid[fqid].append(field)
                else:
                    missing_fields_per_fqid[fqid] = []
            elif fqid in self.cached_missing_fields:
                remaining_missing_fields = [
                    field
                    for field in mapped_fields
                    if field not in self.cached_missing_fields[fqid]
                ]
                if remaining_missing_fields:
                    missing_fields_per_fqid[fqid] = remaining_missing_fields
                else:
                    results[collection_from_fqid(fqid)][id_from_fqid(fqid)] = dict()
            else:
                missing_fields_per_fqid[fqid] = mapped_fields
        return (results, missing_fields_per_fqid)

    def _fetch_missing_fields_from_datastore_for_cache(
        self, missing_fields_per_fqid: MappedFieldsPerFqid, lock_result: bool
    ) -> dict[Collection, dict[int, PartialModel]]:
        get_many_requests = [
            GetManyRequest(collection_from_fqid(fqid), [id_from_fqid(fqid)], fields)
            for fqid, fields in missing_fields_per_fqid.items()
        ]
        results = super().get_many(get_many_requests, lock_result=lock_result)
        return results

    def _update_cache(
        self, fqid: FullQualifiedId, model: dict[str, Any], missing_fields: list[str]
    ) -> None:
        for field in missing_fields:
            if field in model:
                self.cached_models[fqid][field] = model[field]
            else:
                self.cached_missing_fields[fqid].add(field)
