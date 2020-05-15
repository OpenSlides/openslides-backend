from typing import Dict, List

import openslides_backend.services.database.commands as commands
from openslides_backend.services.database.adapter.interface import GetManyRequest
from openslides_backend.services.database.engine import Engine
from openslides_backend.shared.interfaces import Filter, LoggingModule
from openslides_backend.shared.patterns import Collection, FullQualifiedId

from .interface import Aggregate, Count, Found, PartialModel


class Adapter:
    """
    Adapter to connect to (read-only) database.
    """

    def __init__(self, adapter: Engine, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.adapter = adapter

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        command = commands.Get(fqid=fqid, mappedFields=mapped_fields)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.get(command)
        return response

    def getMany(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[str, Dict[int, PartialModel]]:
        command = commands.GetMany(
            get_many_requests=get_many_requests,
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.getMany(command)
        return response

    def getManyByFQIDs(
        self, ids: List[FullQualifiedId],
    ) -> Dict[str, Dict[int, PartialModel]]:
        command = commands.GetManyByFQIDs(ids=ids,)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.getMany(command)
        return response

    def getAll(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        command = commands.GetAll(collection=collection, mapped_fields=mapped_fields)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.getAll(command)
        return response

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        command = commands.Filters(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.filter(command)
        return response

    def exists(self, collection: Collection, filter: Filter) -> Found:
        command = commands.Exists(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.exists(command)
        return {"exists": response["exists"], "position": response["position"]}

    def count(self, collection: Collection, filter: Filter) -> Count:
        command = commands.Count(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.count(command)
        return {"count": response["count"], "position": response["position"]}

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        command = commands.Min(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.min(command)
        return response

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        command = commands.Max(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.max(command)
        return response
